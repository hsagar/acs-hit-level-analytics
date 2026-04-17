"""AWS Lambda entry point for the Search Keyword Revenue pipeline.

Triggered by S3 ObjectCreated events on the raw/ prefix of the raw bucket.
Downloads the TSV file -> Runs the pipeline -> Uploads the report to the processed bucket -> Archives the input file.
"""

import logging
import os
from urllib.parse import unquote_plus

import boto3
from botocore.exceptions import ClientError

from search_keyword_revenue.parser import HitLevelParser
from search_keyword_revenue.writer import ReportWriter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")


def handler(event, context):
    """Handle an S3 ObjectCreated event and run the SKR pipeline."""
    # Parse event payload
    try:
        record = event["Records"][0]["s3"]
        bucket = record["bucket"]["name"]
        key = unquote_plus(record["object"]["key"])
    except (KeyError, IndexError) as e:
        logger.error("Malformed S3 event payload: %s", e)
        return {"statusCode": 400, "body": f"Bad event payload: {e}"}

    logger.info("Processing s3://%s/%s", bucket, key)

    # 1. Download TSV from S3
    local_input = f"/tmp/{os.path.basename(key)}"
    try:
        s3_client.download_file(bucket, key, local_input)
    except ClientError as e:
        error_code = e.response["Error"]["Code"]
        if error_code in ("404", "NoSuchKey"):
            logger.error("Input file not found: s3://%s/%s", bucket, key)
            return {"statusCode": 404, "body": f"File not found: s3://{bucket}/{key}"}
        logger.error("Failed to download s3://%s/%s: %s", bucket, key, e)
        raise
    logger.info("Downloaded to %s", local_input)

    # 2. Run parsing pipeline
    try:
        result = HitLevelParser().run(local_input)
    except ValueError as e:
        logger.error("Pipeline failed — invalid input data: %s", e)
        return {"statusCode": 422, "body": f"Invalid input: {e}"}
    logger.info("Pipeline complete — %d rows in result", len(result))

    output_path = ReportWriter().write(result, "/tmp")
    output_filename = os.path.basename(output_path)
    logger.info("Report written to %s", output_path)

    # 3. Upload the report to the processed bucket
    try:
        processed_bucket = os.environ["PROCESSED_BUCKET"]
    except KeyError:
        logger.error("PROCESSED_BUCKET environment variable is not set")
        return {"statusCode": 500, "body": "Missing PROCESSED_BUCKET env var"}

    s3_key_out = f"processed/{output_filename}"
    try:
        s3_client.upload_file(output_path, processed_bucket, s3_key_out)
    except ClientError as e:
        logger.error("Failed to upload report to s3://%s/%s: %s", processed_bucket, s3_key_out, e)
        raise
    logger.info("Output uploaded to s3://%s/%s", processed_bucket, s3_key_out)

    # 4. Archive the input file (best-effort — report is already saved)
    archive_key = key.replace("raw/", "archive/", 1)
    try:
        s3_client.copy_object(
            Bucket=bucket,
            CopySource={"Bucket": bucket, "Key": key},
            Key=archive_key,
        )
        s3_client.delete_object(Bucket=bucket, Key=key)
        logger.info("Input archived to s3://%s/%s", bucket, archive_key)
    except ClientError as e:
        logger.warning("Archive step failed (report was saved successfully): %s", e)

    return {
        "statusCode": 200,
        "body": f"Processed: {output_filename}",
    }
