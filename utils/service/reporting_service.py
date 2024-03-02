import pandas as pd
from io import BytesIO

class ReportingService:
    def generate_report(self, data):
        df = pd.DataFrame(data)
        return df

    def export_report(self, report_df, format='csv'):
        """
        Export the generated report in the specified format.
        """
        if format == 'csv':
            return self.export_csv(report_df)
        elif format == 'excel':
            return self.export_excel(report_df)
        elif format == 'pdf':
            return self.export_pdf(report_df)
        else:
            raise ValueError("Unsupported export format.")

    def export_csv(self, report_df):
        """
        Export the report DataFrame to CSV format.
        """
        csv_data = report_df.to_csv(index=False)
        return csv_data.encode('utf-8')

    def export_excel(self, report_df):
        """
        Export the report DataFrame to Excel format.
        """
        excel_data = BytesIO()
        with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
            report_df.to_excel(writer, index=False)
        excel_data.seek(0)
        return excel_data.getvalue()
