"""Command-line interface for search-keyword-revenue."""

import argparse
import logging
import sys

from search_keyword_revenue.parser import HitLevelParser
from search_keyword_revenue.writer import ReportWriter

logger = logging.getLogger(__name__)

def main() -> None:
    """Entry point for the skr CLI tool."""
    logging.basicConfig(level=logging.DEBUG)

    parser = argparse.ArgumentParser(
        prog='skr',
        description='Analyse Adobe Analytics hit-level TSV data and report revenue by search keyword.',
    )
    parser.add_argument(
        'input_file',
        help='Path to the hit-level TSV input file.',
    )
    parser.add_argument(
        '--output-dir',
        default='.',
        help='Directory to write the output .tab report (default: current directory).',
    )

    args = parser.parse_args()

    try:
        result = HitLevelParser().run(args.input_file)
    except Exception as e:
        print(f'Error: {e}', file=sys.stderr)
        logger.error('Failed to process input file %r: %s', args.input_file, e)
        sys.exit(1)

    output_path = ReportWriter().write(result, args.output_dir)

    logger.info(result.to_string(index=False))
    logger.info(f'\nRows in report : {len(result)}')
    logger.info(f'Output written : {output_path}')


if __name__ == '__main__':
    main()
