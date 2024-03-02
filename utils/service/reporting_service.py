import pandas as pd
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
class ReportingService:
    def generate_report(self, data):
        df = pd.DataFrame(data)
        return df

    def export_report(self, report_df, format='csv'):
        if format == 'csv':
            return self.export_csv(report_df)
        elif format == 'excel':
            return self.export_excel(report_df)
        elif format == 'pdf':
            return self.export_pdf(report_df)
        else:
            raise ValueError("Unsupported export format.")

    def export_csv(self, report_df):
        csv_data = report_df.to_csv(index=False)
        return csv_data.encode('utf-8')

    def export_excel(self, report_df):
        excel_data = BytesIO()
        with pd.ExcelWriter(excel_data, engine='xlsxwriter') as writer:
            report_df.to_excel(writer, index=False)
        excel_data.seek(0)
        return excel_data.getvalue()


    def export_pdf(self, report_df, filename):
        doc = SimpleDocTemplate(filename, pagesize=letter)
        report_data = [report_df.columns.tolist()] + report_df.values.tolist()
        table = Table(data=report_data)

        style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                            ('GRID', (0, 0), (-1, -1), 1, colors.black)])

        table.setStyle(style)
        doc.build([table])
