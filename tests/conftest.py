"""Shared pytest fixtures providing small, representative DataFrames.

Each fixture isolates a single behaviour so tests remain focused.
"""

import pandas as pd
import pytest

# Base timestamps
_T0 = 1776384000   # 2026-04-17 00:00:00
_T1 = 1776384099   # 2026-04-17 00:01:39
_T2 = 1776384198   # 2026-04-17 00:03:18
_T3 = 1776384297   # 2026-04-17 00:04:57
_T4 = 1776384396   # 2026-04-17 00:06:36

_DT0 = "2026-04-17 00:00:00"
_DT1 = "2026-04-17 00:01:39"
_DT2 = "2026-04-17 00:03:18"
_DT3 = "2026-04-17 00:04:57"
_DT4 = "2026-04-17 00:06:36"

# IP ranges for examples/tests:
# 192.0.2.0/24
# 198.51.100.0/24
# 203.0.113.0/24


def _make_df(rows: list[dict[str, str]]) -> pd.DataFrame:
    """Build a DataFrame from a list of row dicts, filling absent columns with defaults."""
    defaults: dict[str, str] = {
        "hit_time_gmt": str(_T0),
        "date_time": _DT0,
        "user_agent": "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_4_11; en) AppleWebKit/525.27.1",
        "ip": "192.0.2.1",
        "event_list": "",
        "geo_city": "Newark",
        "geo_region": "CA",
        "geo_country": "US",
        "pagename": "Home",
        "page_url": "http://store.example.com",
        "product_list": "",
        "referrer": "",
    }
    data = [{**defaults, **row} for row in rows]
    return pd.DataFrame(data)


@pytest.fixture
def single_purchase_from_google() -> pd.DataFrame:
    """IP searches on Google, views product, purchases. Simple happy path."""
    return _make_df([
        {
            "hit_time_gmt": str(_T0),
            "date_time": _DT0,
            "ip": "192.0.2.10",
            "referrer": "http://www.google.com/search?q=Ipod",
        },
        {
            "hit_time_gmt": str(_T1),
            "date_time": _DT1,
            "ip": "192.0.2.10",
            "referrer": "http://store.example.com/electronics",
        },
        {
            "hit_time_gmt": str(_T2),
            "date_time": _DT2,
            "ip": "192.0.2.10",
            "event_list": "1",
            "product_list": "Electronics;Ipod Touch 32GB;1;290.00;1",
        },
    ])


@pytest.fixture
def two_ips_different_engines() -> pd.DataFrame:
    """IP-A from Google buys product-A. IP-B from Bing buys product-B."""
    return _make_df([
        {
            "hit_time_gmt": str(_T0),
            "date_time": _DT0,
            "ip": "198.51.100.11",
            "referrer": "http://www.google.com/search?q=ipod",
        },
        {
            "hit_time_gmt": str(_T1),
            "date_time": _DT1,
            "ip": "198.51.100.11",
            "event_list": "1",
            "product_list": "Electronics;Ipod;1;290.00;1",
        },
        {
            "hit_time_gmt": str(_T2),
            "date_time": _DT2,
            "ip": "198.51.100.12",
            "referrer": "http://www.bing.com/search?q=zune",
        },
        {
            "hit_time_gmt": str(_T3),
            "date_time": _DT3,
            "ip": "198.51.100.12",
            "event_list": "1",
            "product_list": "Electronics;Zune;1;250.00;1",
        },
    ])


@pytest.fixture
def se_referrer_then_internal_navigation() -> pd.DataFrame:
    """SE referral → 3 internal page views → purchase. Tests ffill."""
    return _make_df([
        {
            "hit_time_gmt": str(_T0),
            "date_time": _DT0,
            "ip": "203.0.113.20",
            "referrer": "http://www.google.com/search?q=widget",
        },
        {
            "hit_time_gmt": str(_T1),
            "date_time": _DT1,
            "ip": "203.0.113.20",
            "referrer": "http://store.example.com/home",
        },
        {
            "hit_time_gmt": str(_T2),
            "date_time": _DT2,
            "ip": "203.0.113.20",
            "referrer": "http://store.example.com/category",
        },
        {
            "hit_time_gmt": str(_T3),
            "date_time": _DT3,
            "ip": "203.0.113.20",
            "referrer": "http://store.example.com/product",
        },
        {
            "hit_time_gmt": str(_T4),
            "date_time": _DT4,
            "ip": "203.0.113.20",
            "event_list": "1",
            "product_list": "Tools;Widget Pro;1;150.00;1",
        },
    ])


@pytest.fixture
def multiple_products_in_purchase() -> pd.DataFrame:
    """product_list has two products separated by comma. Revenue = sum of both."""
    return _make_df([
        {
            "hit_time_gmt": str(_T0),
            "date_time": _DT0,
            "ip": "192.0.2.30",
            "referrer": "http://www.google.com/search?q=bundle",
        },
        {
            "hit_time_gmt": str(_T1),
            "date_time": _DT1,
            "ip": "192.0.2.30",
            "event_list": "1",
            "product_list": "Electronics;Gadget A;1;100.00;1,Electronics;Gadget B;1;50.00;1",
        },
    ])


@pytest.fixture
def purchase_no_se_referrer() -> pd.DataFrame:
    """Purchase event fires but IP never had an SE referrer. Should be excluded."""
    return _make_df([
        {
            "hit_time_gmt": str(_T0),
            "date_time": _DT0,
            "ip": "198.51.100.40",
            "referrer": "http://store.example.com/home",
        },
        {
            "hit_time_gmt": str(_T1),
            "date_time": _DT1,
            "ip": "198.51.100.40",
            "event_list": "1",
            "product_list": "Electronics;Direct Buy;1;199.00;1",
        },
    ])


@pytest.fixture
def zero_revenue_purchase() -> pd.DataFrame:
    """event_list=1, product_list present but revenue field is empty."""
    return _make_df([
        {
            "hit_time_gmt": str(_T0),
            "date_time": _DT0,
            "ip": "203.0.113.50",
            "referrer": "http://www.google.com/search?q=laptop",
        },
        {
            "hit_time_gmt": str(_T1),
            "date_time": _DT1,
            "ip": "203.0.113.50",
            "event_list": "1",
            "product_list": "Electronics;Laptop;1;;1",
        },
    ])


@pytest.fixture
def negative_revenue() -> pd.DataFrame:
    """Revenue field is -50.00. Should be included as-is (e.g. refund row)."""
    return _make_df([
        {
            "hit_time_gmt": str(_T0),
            "date_time": _DT0,
            "ip": "192.0.2.60",
            "referrer": "http://www.google.com/search?q=refund",
        },
        {
            "hit_time_gmt": str(_T1),
            "date_time": _DT1,
            "ip": "192.0.2.60",
            "event_list": "1",
            "product_list": "Electronics;Returned Item;1;-50.00;1",
        },
    ])


@pytest.fixture
def unsorted_hits() -> pd.DataFrame:
    """Rows are intentionally out of hit_time_gmt order."""
    return _make_df([
        {
            "hit_time_gmt": str(_T2),
            "date_time": _DT2,  # purchase listed first
            "ip": "198.51.100.70",
            "event_list": "1",
            "product_list": "Electronics;Widget;1;100.00;1",
        },
        {
            "hit_time_gmt": str(_T1),
            "date_time": _DT1,
            "ip": "198.51.100.70",
            "referrer": "http://store.example.com/category",
        },
        {
            "hit_time_gmt": str(_T0),
            "date_time": _DT0,  # SE referrer listed last
            "ip": "198.51.100.70",
            "referrer": "http://www.google.com/search?q=widget",
        },
    ])


@pytest.fixture
def url_encoded_keyword() -> pd.DataFrame:
    """Referrer has q=cd+player. Keyword should decode to 'cd player'."""
    return _make_df([
        {
            "hit_time_gmt": str(_T0),
            "date_time": _DT0,
            "ip": "203.0.113.80",
            "referrer": "http://www.google.com/search?q=cd+player",
        },
        {
            "hit_time_gmt": str(_T1),
            "date_time": _DT1,
            "ip": "203.0.113.80",
            "event_list": "1",
            "product_list": "Music;CD Player;1;49.99;1",
        },
    ])


@pytest.fixture
def yahoo_p_param() -> pd.DataFrame:
    """Yahoo referrer uses p= not q=."""
    return _make_df([
        {
            "hit_time_gmt": str(_T0),
            "date_time": _DT0,
            "ip": "192.0.2.81",
            "referrer": "http://search.yahoo.com/search?p=walkman",
        },
        {
            "hit_time_gmt": str(_T1),
            "date_time": _DT1,
            "ip": "192.0.2.81",
            "event_list": "1",
            "product_list": "Electronics;Walkman;1;39.99;1",
        },
    ])


@pytest.fixture
def malformed_referrer() -> pd.DataFrame:
    """referrer is 'not a url at all'. Should not crash."""
    return _make_df([
        {
            "hit_time_gmt": str(_T0),
            "date_time": _DT0,
            "ip": "198.51.100.90",
            "referrer": "not a url at all",
        },
        {
            "hit_time_gmt": str(_T1),
            "date_time": _DT1,
            "ip": "198.51.100.90",
            "event_list": "1",
            "product_list": "Electronics;Widget;1;100.00;1",
        },
    ])


@pytest.fixture
def null_referrer() -> pd.DataFrame:
    """referrer field is NaN/empty. Should not overwrite stored SE."""
    return _make_df([
        {
            "hit_time_gmt": str(_T0),
            "date_time": _DT0,
            "ip": "203.0.113.91",
            "referrer": "http://www.google.com/search?q=ipod",
        },
        {
            "hit_time_gmt": str(_T1),
            "date_time": _DT1,
            "ip": "203.0.113.91",
            "referrer": "",
        },
        {
            "hit_time_gmt": str(_T2),
            "date_time": _DT2,
            "ip": "203.0.113.91",
            "event_list": "1",
            "product_list": "Electronics;Ipod;1;190.00;1",
        },
    ])


@pytest.fixture
def subdomain_referrer() -> pd.DataFrame:
    """Referrer is images.google.com with q= param. Should match google.com."""
    return _make_df([
        {
            "hit_time_gmt": str(_T0),
            "date_time": _DT0,
            "ip": "192.0.2.92",
            "referrer": "http://images.google.com/search?q=camera",
        },
        {
            "hit_time_gmt": str(_T1),
            "date_time": _DT1,
            "ip": "192.0.2.92",
            "event_list": "1",
            "product_list": "Electronics;Camera;1;299.00;1",
        },
    ])


@pytest.fixture
def case_sensitive_keywords() -> pd.DataFrame:
    """IP-A searches 'Ipod' (uppercased), IP-B searches 'ipod'. Pipeline lowercases both."""
    return _make_df([
        {
            "hit_time_gmt": str(_T0),
            "date_time": _DT0,
            "ip": "198.51.100.93",
            "referrer": "http://www.google.com/search?q=Ipod",
        },
        {
            "hit_time_gmt": str(_T1),
            "date_time": _DT1,
            "ip": "198.51.100.93",
            "event_list": "1",
            "product_list": "Electronics;Ipod;1;290.00;1",
        },
        {
            "hit_time_gmt": str(_T2),
            "date_time": _DT2,
            "ip": "198.51.100.94",
            "referrer": "http://www.google.com/search?q=ipod",
        },
        {
            "hit_time_gmt": str(_T3),
            "date_time": _DT3,
            "ip": "198.51.100.94",
            "event_list": "1",
            "product_list": "Electronics;Ipod Nano;1;190.00;1",
        },
    ])


@pytest.fixture
def duplicate_rows() -> pd.DataFrame:
    """Same row appears twice. Revenue should not be double-counted."""
    row: dict[str, str] = {
        "hit_time_gmt": str(_T0),
        "date_time": _DT0,
        "ip": "203.0.113.95",
        "referrer": "http://www.google.com/search?q=gadget",
        "event_list": "1",
        "product_list": "Electronics;Gadget;1;199.00;1",
    }
    return _make_df([row, row])
