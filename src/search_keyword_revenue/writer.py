"""Report writer for search keyword revenue output."""

import datetime
import os

import pandas as pd


class ReportWriter:
    """Writes the aggregated revenue report to a tab-delimited .tab file."""

    def write(self, df: pd.DataFrame, output_dir: str) -> str:
        """Write the report and return the full output file path.
        
        The filename format is: [YYYY-mm-dd]_SearchKeywordPerformance.tab
        """
        
        today = datetime.date.today().strftime('%Y-%m-%d')
        filename = f'[{today}]_SearchKeywordPerformance.tab'
        output_path = os.path.join(output_dir, filename)
        
        df.to_csv(output_path, sep='\t', index=False)
        return output_path
