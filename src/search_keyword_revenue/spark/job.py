"""PySpark hit-level parser for search keyword revenue attribution.

Mirrors the pandas HitLevelParser pipeline using Spark DataFrames.
Pure functions from parser.py are reused as UDFs.
"""

import os

from pyspark.sql import DataFrame, SparkSession
from pyspark.sql import functions as F
from pyspark.sql.types import BooleanType, FloatType, StringType, StructField, StructType
from pyspark.sql.window import Window

from search_keyword_revenue.config import REQUIRED_COLUMNS
from search_keyword_revenue.parser import is_purchase, parse_revenue, parse_search_referrer

_referrer_schema = StructType(
    [
        StructField("se_domain", StringType()),
        StructField("se_keyword", StringType()),
    ]
)


def _referrer_udf_fn(referrer: str):
    return parse_search_referrer(referrer)


def _revenue_udf_fn(product_list: str):
    return parse_revenue(product_list)


def _is_purchase_udf_fn(event_list: str):
    return is_purchase(event_list)


_parse_referrer_udf = F.udf(_referrer_udf_fn, _referrer_schema)
_parse_revenue_udf = F.udf(_revenue_udf_fn, FloatType())
_is_purchase_udf = F.udf(_is_purchase_udf_fn, BooleanType())


class SparkHitLevelJob:
    """PySpark version of HitLevelParser.

    Known limitations (v1):
    - Session is keyed by IP only; shared IPs (NAT) will conflate sessions.
    - Attribution model is last-touch: the most recent SE referrer before purchase wins.
    """

    def __init__(self, spark: SparkSession) -> None:
        self.spark = spark

    def run(self, filepath: str) -> DataFrame:
        """Execute the full pipeline and return the aggregated result DataFrame."""
        df = self._load(filepath)
        self._validate_columns(df)

        df = self._sort_by_time(df)
        df = self._parse_referrers(df)
        df = self._propagate_referrers(df)
        df = self._filter_purchases(df)
        df = self._parse_revenue(df)

        return self._aggregate(df)

    def _load(self, filepath: str) -> DataFrame:
        abs_path = os.path.abspath(filepath)

        print(f"Loading data from {abs_path}...")
        return (
            self.spark.read.option("header", "true")
            .option("sep", "\t")
            .option("inferSchema", "false")
            .csv(f"file://{abs_path}")
            .dropDuplicates()
        )

    def _validate_columns(self, df: DataFrame) -> None:
        missing = set(REQUIRED_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def _sort_by_time(self, df: DataFrame) -> DataFrame:
        return df.withColumn("hit_time_gmt", F.col("hit_time_gmt").cast("long")).orderBy("hit_time_gmt")

    def _parse_referrers(self, df: DataFrame) -> DataFrame:
        df = df.withColumn("referrer", F.lower(F.col("referrer")))

        parsed = _parse_referrer_udf(F.col("referrer"))

        return df.withColumn("se_domain", parsed["se_domain"]).withColumn("se_keyword", parsed["se_keyword"])

    def _propagate_referrers(self, df: DataFrame) -> DataFrame:
        """Forward-fill SE referrer within each IP group (last-touch attribution)."""
        window = Window.partitionBy("ip").orderBy("hit_time_gmt").rowsBetween(Window.unboundedPreceding, 0)

        return df.withColumn("se_domain", F.last("se_domain", ignorenulls=True).over(window)).withColumn(
            "se_keyword", F.last("se_keyword", ignorenulls=True).over(window)
        )

    def _filter_purchases(self, df: DataFrame) -> DataFrame:
        return df.filter(_is_purchase_udf(F.col("event_list")))

    def _parse_revenue(self, df: DataFrame) -> DataFrame:
        return df.withColumn("revenue", _parse_revenue_udf(F.col("product_list")))

    def _aggregate(self, df: DataFrame) -> DataFrame:
        return (
            df.filter(F.col("se_domain").isNotNull() & F.col("se_keyword").isNotNull())
            .groupBy("se_domain", "se_keyword")
            .agg(F.sum("revenue").alias("revenue"))
            .filter(F.col("revenue") != 0)
            .orderBy(F.col("revenue").desc())
            .withColumnRenamed("se_domain", "Search Engine Domain")
            .withColumnRenamed("se_keyword", "Search Keyword")
            .withColumn("Revenue", F.format_number(F.col("revenue"), 2))
            .drop("revenue")
        )
