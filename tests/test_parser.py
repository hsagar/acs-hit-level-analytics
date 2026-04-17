"""Unit tests for HitLevelParser and module-level helper functions."""

from pathlib import Path

import pandas as pd
import pytest

from search_keyword_revenue.parser import (
    HitLevelParser,
    is_purchase,
    parse_revenue,
    parse_search_referrer,
)

# Helpers


def _run_pipeline(df: pd.DataFrame, tmp_path: Path) -> pd.DataFrame:
    """Write fixture to a temp TSV file and execute the full pipeline."""
    input_file = tmp_path / "input.tsv"
    df.to_csv(input_file, sep="\t", index=False)
    return HitLevelParser().run(str(input_file))


# parse_search_referrer


def test_parse_search_referrer_google_returns_domain_and_keyword():
    se_domain, keyword = parse_search_referrer("http://www.google.com/search?q=ipod")

    assert se_domain == "google.com"
    assert keyword == "ipod"


def test_parse_search_referrer_unknown_domain_returns_none_pair():
    se_domain, keyword = parse_search_referrer("http://www.example.com/page?q=test")

    assert se_domain is None
    assert keyword is None


def test_parse_search_referrer_empty_string_returns_none_pair():
    se_domain, keyword = parse_search_referrer("")

    assert se_domain is None
    assert keyword is None


# parse_revenue


def test_parse_revenue_single_product():
    result = parse_revenue("Electronics;Ipod;1;290.00;1")

    assert result == pytest.approx(290.0)


def test_parse_revenue_multiple_products_sums_all():
    result = parse_revenue("Electronics;A;1;100.00;1,Electronics;B;1;50.00;1")

    assert result == pytest.approx(150.0)


def test_parse_revenue_empty_revenue_field_returns_zero():
    result = parse_revenue("Electronics;Laptop;1;;1")

    assert result == pytest.approx(0.0)


def test_parse_revenue_negative_value_returned_as_is():
    result = parse_revenue("Electronics;Refund;1;-50.00;1")

    assert result == pytest.approx(-50.0)


def test_parse_revenue_empty_string_returns_zero():
    result = parse_revenue("")

    assert result == pytest.approx(0.0)


# is_purchase


def test_is_purchase_event_1_present_returns_true():
    assert is_purchase("1") is True


def test_is_purchase_event_1_in_list_returns_true():
    assert is_purchase("2,1,3") is True


def test_is_purchase_event_1_absent_returns_false():
    assert is_purchase("2,3") is False


def test_is_purchase_empty_string_returns_false():
    assert is_purchase("") is False


def test_is_purchase_does_not_match_composite_event_id():
    assert is_purchase("10,11") is False


# HitLevelParser — pipeline integration tests


def test_happy_path_single_purchase(single_purchase_from_google: pd.DataFrame, tmp_path: Path):
    result = _run_pipeline(single_purchase_from_google, tmp_path)

    assert len(result) == 1
    assert result.iloc[0]["Search Engine Domain"] == "google.com"
    # pipeline lowercases the full referrer URL before parsing, so keyword is lowercase
    assert result.iloc[0]["Search Keyword"] == "ipod"
    assert result.iloc[0]["Revenue"] == "290.00"


def test_revenue_attributed_after_internal_navigation(
    se_referrer_then_internal_navigation: pd.DataFrame, tmp_path: Path
):
    result = _run_pipeline(se_referrer_then_internal_navigation, tmp_path)

    assert len(result) == 1
    assert result.iloc[0]["Search Engine Domain"] == "google.com"
    assert result.iloc[0]["Search Keyword"] == "widget"
    assert result.iloc[0]["Revenue"] == "150.00"


def test_two_ips_attributed_independently(two_ips_different_engines: pd.DataFrame, tmp_path: Path):
    result = _run_pipeline(two_ips_different_engines, tmp_path)

    domains = set(result["Search Engine Domain"])
    assert domains == {"google.com", "bing.com"}
    assert len(result) == 2


def test_purchase_without_se_referrer_excluded(purchase_no_se_referrer: pd.DataFrame, tmp_path: Path):
    result = _run_pipeline(purchase_no_se_referrer, tmp_path)

    assert len(result) == 0


def test_zero_revenue_purchase_excluded(zero_revenue_purchase: pd.DataFrame, tmp_path: Path):
    result = _run_pipeline(zero_revenue_purchase, tmp_path)

    assert len(result) == 0


def test_negative_revenue_included(negative_revenue: pd.DataFrame, tmp_path: Path):
    result = _run_pipeline(negative_revenue, tmp_path)

    assert len(result) == 1
    assert result.iloc[0]["Revenue"] == "-50.00"


def test_unsorted_input_sorted_before_processing(unsorted_hits: pd.DataFrame, tmp_path: Path):
    result = _run_pipeline(unsorted_hits, tmp_path)

    assert len(result) == 1
    assert result.iloc[0]["Search Engine Domain"] == "google.com"
    assert result.iloc[0]["Revenue"] == "100.00"


def test_url_encoded_keyword_decoded(url_encoded_keyword: pd.DataFrame, tmp_path: Path):
    result = _run_pipeline(url_encoded_keyword, tmp_path)

    assert len(result) == 1
    assert result.iloc[0]["Search Keyword"] == "cd player"


def test_yahoo_uses_p_param(yahoo_p_param: pd.DataFrame, tmp_path: Path):
    result = _run_pipeline(yahoo_p_param, tmp_path)

    assert len(result) == 1
    assert result.iloc[0]["Search Engine Domain"] == "yahoo.com"
    assert result.iloc[0]["Search Keyword"] == "walkman"


def test_malformed_referrer_does_not_crash(malformed_referrer: pd.DataFrame, tmp_path: Path):
    result = _run_pipeline(malformed_referrer, tmp_path)

    assert isinstance(result, pd.DataFrame)


def test_null_referrer_does_not_overwrite_se(null_referrer: pd.DataFrame, tmp_path: Path):
    result = _run_pipeline(null_referrer, tmp_path)

    assert len(result) == 1
    assert result.iloc[0]["Search Engine Domain"] == "google.com"
    assert result.iloc[0]["Search Keyword"] == "ipod"


def test_subdomain_matches_parent_engine(subdomain_referrer: pd.DataFrame, tmp_path: Path):
    result = _run_pipeline(subdomain_referrer, tmp_path)

    assert len(result) == 1
    assert result.iloc[0]["Search Engine Domain"] == "google.com"


def test_keywords_lowercased_by_pipeline(case_sensitive_keywords: pd.DataFrame, tmp_path: Path):
    # The pipeline lowercases the full referrer URL before parsing, so q=Ipod
    # and q=ipod both produce keyword "ipod". The two IPs aggregate into one row.
    result = _run_pipeline(case_sensitive_keywords, tmp_path)

    assert len(result) == 1
    assert result.iloc[0]["Search Keyword"] == "ipod"
    assert result.iloc[0]["Revenue"] == "480.00"


def test_multiple_products_revenue_summed(multiple_products_in_purchase: pd.DataFrame, tmp_path: Path):
    result = _run_pipeline(multiple_products_in_purchase, tmp_path)

    assert len(result) == 1
    assert result.iloc[0]["Revenue"] == "150.00"


def test_missing_required_column_raises_value_error(tmp_path: Path):
    df = pd.DataFrame({"ip": ["1.2.3.4"], "referrer": ["http://google.com?q=test"]})
    input_file = tmp_path / "input.tsv"
    df.to_csv(input_file, sep="\t", index=False)

    with pytest.raises(ValueError, match="Missing required columns"):
        HitLevelParser().run(str(input_file))


def test_output_sorted_by_revenue_descending(two_ips_different_engines: pd.DataFrame, tmp_path: Path):
    result = _run_pipeline(two_ips_different_engines, tmp_path)

    revenues = result["Revenue"].tolist()
    assert revenues == sorted(revenues, reverse=True)


def test_output_columns_named_correctly(single_purchase_from_google: pd.DataFrame, tmp_path: Path):
    result = _run_pipeline(single_purchase_from_google, tmp_path)

    assert list(result.columns) == ["Search Engine Domain", "Search Keyword", "Revenue"]


def test_duplicate_rows_revenue_not_double_counted(duplicate_rows: pd.DataFrame, tmp_path: Path):
    result = _run_pipeline(duplicate_rows, tmp_path)

    assert len(result) == 1
    assert result.iloc[0]["Revenue"] == "199.00"
