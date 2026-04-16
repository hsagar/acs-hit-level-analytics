"""Hit-level data parser for search keyword revenue attribution.

Pipeline: load → validate → sort → parse referrers → propagate (ffill) →
          filter purchases → parse revenue → aggregate
"""

import logging
from urllib.parse import parse_qs, urlparse

import pandas as pd

from search_keyword_revenue.config import EVENT_TYPES, REQUIRED_COLUMNS, SEARCH_ENGINES

logger = logging.getLogger(__name__)


def normalize_domain(hostname: str) -> str:
    """Normalize a hostname to its base domain

    Examples:
    (www.google.com -> google.com, images.google.com -> google.com, serach.yahoo.com -> yahoo.com)
    """
    if not hostname:
        return ''

    parts = hostname.lower().split('.')

    return hostname.lower() if len(parts) == 1 else '.'.join(parts[-2:])


def parse_search_referrer(referrer: str) -> tuple:
    """Parse a referrer URL and return (se_domain, keyword) for known search engines.

    Returns (None, None) if the referrer is not a recognised search engine URL.
    URL decoding (including + → space) is handled by urllib.parse.parse_qs.
    """
    if not referrer:
        return None, None

    try:
        parsed = urlparse(referrer)
        net_loc = normalize_domain(parsed.hostname or '')

        matched_engine: str | None = None
        for domain in SEARCH_ENGINES:
            if net_loc == domain:
                matched_engine = domain
                break

        if matched_engine is None:
            return None, None

        params = parse_qs(parsed.query)
        param_key = SEARCH_ENGINES[matched_engine]
        values = params.get(param_key, [])

        if not values:
            return matched_engine, None

        return matched_engine, values[0]

    except Exception as exc:
        logger.warning('Failed to parse referrer %r: %s', referrer, exc)
        return None, None


def parse_revenue(product_list: str) -> float:
    """Sum revenue from a semicolon/comma-delimited product_list string.

    Format per product: Category;Name;Qty;Revenue;Events
    Multiple products are comma-separated.
    Empty or non-numeric revenue fields are silently skipped.
    """
    if not product_list:
        return 0.0

    total = 0.0
    for product in product_list.split(','):
        parts = product.split(';')
        if len(parts) > 3:
            revenue_str = parts[3].strip()
            if revenue_str:
                try:
                    total += float(revenue_str)
                except ValueError:
                    logger.warning('Could not parse revenue value %r in product_list', revenue_str)

    return total


def is_purchase(event_list: str) -> bool:
    """Return True if the purchase event is present in event_list."""
    if not event_list:
        return False

    return EVENT_TYPES.purchase in event_list.split(',')


class HitLevelParser:
    """Parses Adobe Analytics hit-level TSV data and aggregates revenue by search keyword.

    Known limitations (v1):
    - Session is keyed by IP only; shared IPs (NAT) will conflate sessions.
    - Attribution model is last-touch: the most recent SE referrer before purchase wins.
    """

    def run(self, filepath: str) -> pd.DataFrame:
        """Execute the full parsing pipeline and return the aggregated result DataFrame.

        The result has columns: Search Engine Domain, Search Keyword, Revenue,
        sorted by Revenue descending.
        """
        df = self._load(filepath)
        self._validate_columns(df)

        df = self._sort_by_time(df)
        df = self._parse_referrers(df)
        df = self._propagate_referrers(df)
        df = self._filter_purchases(df)
        df = self._parse_revenue(df)

        return self._aggregate(df)

    def _load(self, filepath: str) -> pd.DataFrame:
        df: pd.DataFrame = pd.read_csv(
            filepath,
            sep='\t',
            dtype=str,
            keep_default_na=False,
        )
        return df.drop_duplicates()

    def _validate_columns(self, df: pd.DataFrame) -> None:
        missing = set(REQUIRED_COLUMNS) - set(df.columns)
        if missing:
            raise ValueError(f'Missing required columns: {missing}')

    def _sort_by_time(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['hit_time_gmt'] = pd.to_numeric(df['hit_time_gmt'], errors='coerce')
        return df.sort_values('hit_time_gmt').reset_index(drop=True)

    def _parse_referrers(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['referrer'] = df['referrer'].str.lower().fillna('')

        parsed = df['referrer'].apply(parse_search_referrer)
        df['se_domain'] = [x[0] for x in parsed]
        df['se_keyword'] = [x[1] for x in parsed]

        return df

    def _propagate_referrers(self, df: pd.DataFrame) -> pd.DataFrame:
        """Forward-fill SE referrer within each IP group (last-touch attribution)."""
        df = df.copy()
        df['se_domain'] = df.groupby('ip', sort=False)['se_domain'].ffill()
        df['se_keyword'] = df.groupby('ip', sort=False)['se_keyword'].ffill()
        return df

    # def _propagate_referrers(self, df: pd.DataFrame) -> pd.DataFrame:
    #     """Propagate the first SE referrer seen per IP group (first-touch attribution)."""
    #     df = df.copy()
    #     df["se_domain"] = df.groupby("ip", sort=False)["se_domain"].transform("first")
    #     df["se_keyword"] = df.groupby("ip", sort=False)["se_keyword"].transform("first")
    #     return df

    def _filter_purchases(self, df: pd.DataFrame) -> pd.DataFrame:
        mask = df['event_list'].apply(
            lambda e: is_purchase(e if isinstance(e, str) else '')
        )
        return df[mask].copy()

    def _parse_revenue(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df['revenue'] = df['product_list'].apply(
            lambda p: parse_revenue(p if isinstance(p, str) else '')
        )
        return df

    def _aggregate(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.dropna(subset=['se_domain', 'se_keyword'])

        result: pd.DataFrame = (
            df.groupby(['se_domain', 'se_keyword'], as_index=False)['revenue'].sum()
        )

        result = result[result['revenue'] != 0]
        result = result.sort_values('revenue', ascending=False).reset_index(drop=True)

        result = result.rename(
            columns={
                'se_domain': 'Search Engine Domain',
                'se_keyword': 'Search Keyword',
                'revenue': 'Revenue',
            }
        )

        result['Revenue'] = result['Revenue'].map(lambda x: f'{x:.2f}')

        return result
