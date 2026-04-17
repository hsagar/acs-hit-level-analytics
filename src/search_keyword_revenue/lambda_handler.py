"""AWS Lambda entry point for the Search Keyword Revenue pipeline.

Triggered by S3 ObjectCreated events on the raw/ prefix of the raw bucket.
Downloads the TSV file -> Runs the pipeline -> Uploads the report to the processed bucket -> Archives the input file.
"""

import logging
import os
from urllib.parse import unquote_plus

import boto3

from search_keyword_revenue.parser import HitLevelParser
from search_keyword_revenue.writer import ReportWriter

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

s3_client = boto3.client("s3")


def handler(event, context):
    """Handle an S3 ObjectCreated event and run the SKR pipeline."""
    record = event["Records"][0]["s3"]
    bucket = record["bucket"]["name"]
    key = unquote_plus(record["object"]["key"])

    logger.info("Processing s3://%s/%s", bucket, key)

    # 1. Download TSV from S3
    local_input = f"/tmp/{os.path.basename(key)}"
    s3_client.download_file(bucket, key, local_input)
    logger.info("Downloaded to %s", local_input)

    # 2. Run parsing pipeline
    result = HitLevelParser().run(local_input)
    logger.info("Pipeline complete — %d rows in result", len(result))

    output_path = ReportWriter().write(result, "/tmp")
    output_filename = os.path.basename(output_path)
    logger.info("Report written to %s", output_path)

    # 3. Upload the report to the processed bucket
    processed_bucket = os.environ["PROCESSED_BUCKET"]
    s3_key_out = f"processed/{output_filename}"
    s3_client.upload_file(output_path, processed_bucket, s3_key_out)
    logger.info("Output uploaded to s3://%s/%s", processed_bucket, s3_key_out)

    # 4. Archive the input file
    archive_key = key.replace("raw/", "archive/", 1)
    s3_client.copy_object(
        Bucket=bucket,
        CopySource={"Bucket": bucket, "Key": key},
        Key=archive_key,
    )
    s3_client.delete_object(Bucket=bucket, Key=key)
    logger.info("Input archived to s3://%s/%s", bucket, archive_key)

    return {
        "statusCode": 200,
        "body": f"Processed: {output_filename}",
    }
