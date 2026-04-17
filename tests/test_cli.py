"""Unit tests for the CLI entry point."""

from pathlib import Path
from unittest.mock import patch

import pytest

from search_keyword_revenue.cli import main

DATA_DIR = Path(__file__).parent.parent / "data"


def test_cli_runs_and_prints_report(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    import logging

    input_file = str(DATA_DIR / "sample_input.tsv")

    with patch("sys.argv", ["skr", input_file, "--output-dir", str(tmp_path)]):
        with caplog.at_level(logging.INFO):
            main()

    # CLI uses logger.info — captured via caplog, not capsys
    assert "google.com" in caplog.text
    assert "Output written" in caplog.text


def test_cli_creates_output_file(tmp_path: Path) -> None:
    input_file = str(DATA_DIR / "sample_input.tsv")

    with patch("sys.argv", ["skr", input_file, "--output-dir", str(tmp_path)]):
        main()

    tab_files = list(tmp_path.glob("*.tab"))
    assert len(tab_files) == 1


def test_cli_exits_with_error_on_missing_file(tmp_path: Path) -> None:
    with patch("sys.argv", ["skr", str(tmp_path / "nonexistent.tsv")]):
        with pytest.raises(SystemExit) as ex_info:
            main()
    assert ex_info.value.code == 1


def test_cli_exits_with_error_on_bad_columns(tmp_path: Path) -> None:
    bad_file = tmp_path / "bad.tsv"
    bad_file.write_text("col_a\tcol_b\n1\t2\n")

    with patch("sys.argv", ["skr", str(bad_file)]):
        with pytest.raises(SystemExit) as ex_info:
            main()
    assert ex_info.value.code == 1
