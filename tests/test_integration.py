"""End-to-end integration test against the sample dataset."""

from pathlib import Path

from search_keyword_revenue.parser import HitLevelParser
from search_keyword_revenue.writer import ReportWriter

DATA_DIR = Path(__file__).parent / "data"


def test_end_to_end_matches_expected_output(tmp_path: Path) -> None:
    input_file = DATA_DIR / "sample_input.tsv"
    expected_file = DATA_DIR / "expected_output.tab"

    result = HitLevelParser().run(str(input_file))
    output_path = ReportWriter().write(result, str(tmp_path))

    actual_lines = Path(output_path).read_text().strip().splitlines()
    expected_lines = expected_file.read_text().strip().splitlines()

    assert actual_lines == expected_lines
