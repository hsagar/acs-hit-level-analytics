"""Unit tests for ReportWriter."""

import datetime
from pathlib import Path

import pandas as pd

from search_keyword_revenue.writer import ReportWriter


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "Search Engine Domain": ["google.com", "bing.com"],
            "Search Keyword": ["ipod", "zune"],
            "Revenue": [290.0, 250.0],
        }
    )


def test_output_file_created(tmp_path: Path) -> None:
    output_path = ReportWriter().write(_sample_df(), str(tmp_path))

    assert Path(output_path).exists()


def test_filename_uses_today_date(tmp_path: Path) -> None:
    today = datetime.date.today().strftime("%Y-%m-%d")

    output_path = ReportWriter().write(_sample_df(), str(tmp_path))

    assert today in Path(output_path).name


def test_header_row_correct(tmp_path: Path) -> None:
    output_path = ReportWriter().write(_sample_df(), str(tmp_path))

    with open(output_path) as f:
        header = f.readline().strip()

    assert header == "Search Engine Domain\tSearch Keyword\tRevenue"


def test_tab_delimiter_used(tmp_path: Path) -> None:
    output_path = ReportWriter().write(_sample_df(), str(tmp_path))

    with open(output_path) as f:
        header = f.readline()

    assert "\t" in header
    assert "," not in header


def test_rows_in_correct_order(tmp_path: Path) -> None:
    output_path = ReportWriter().write(_sample_df(), str(tmp_path))

    with open(output_path) as f:
        lines = f.readlines()

    assert "google.com" in lines[1]
    assert "bing.com" in lines[2]
