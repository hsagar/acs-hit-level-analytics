"""Spark command-line interface for search-keyword-revenue."""

import argparse
import logging
import sys

from pyspark.sql import SparkSession

from search_keyword_revenue.spark.job import SparkHitLevelJob


def main() -> None:
    """Entry point for the skr-spark CLI tool."""
    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(
        prog="skr-spark",
        description="Analyse Adobe Analytics hit-level TSV data and report revenue by search keyword using PySpark.",
    )
    parser.add_argument(
        "input_file",
        help="Path to the hit-level TSV input file.",
    )
    parser.add_argument(
        "--output-dir",
        default=".",
        help="Directory to write the output report (default: current directory).",
    )
    parser.add_argument(
        "--app-name",
        default="SearchKeywordRevenue",
        help="Spark application name (default: SearchKeywordRevenue).",
    )

    args = parser.parse_args()

    spark = (
        SparkSession.builder.appName(args.app_name)
        .config("spark.hadoop.fs.file.impl", "org.apache.hadoop.fs.RawLocalFileSystem")
        .getOrCreate()
    )

    spark.sparkContext.setLogLevel("ERROR")

    try:
        result = SparkHitLevelJob(spark).run(args.input_file)
    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        spark.stop()
        sys.exit(1)

    output_path = f"{args.output_dir}/SearchKeywordPerformance"
    (result.coalesce(1).write.option("header", "true").option("sep", "\t").mode("overwrite").csv(output_path))

    result.show(truncate=False)
    print(f"\nOutput written : {output_path}")

    spark.stop()


if __name__ == "__main__":
    main()
