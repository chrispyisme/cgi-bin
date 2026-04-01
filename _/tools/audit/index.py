import google.generativeai as genai
import pandas as pd

class GeminiAuditTool:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
    
    def audit_csv(self, filepath, audit_criteria):
        """Audit a CSV file"""
        df = pd.read_csv(filepath)
        
        data_summary = f"""
        Rows: {len(df)}
        Columns: {list(df.columns)}
        Sample data:
        {df.head(10).to_string()}
        
        Full data:
        {df.to_string()}
        """
        
        prompt = f"""Audit this data based on these criteria:
        {audit_criteria}
        
        Data to audit:
        {data_summary}
        
        Provide:
        1. Issues found
        2. Severity (High/Medium/Low)
        3. Recommendations
        """
        
        response = self.model.generate_content(prompt)
        return response.text
    
    def audit_pdf(self, filepath, audit_criteria):
        """Audit a PDF file"""
        # Upload the PDF file
        uploaded_file = genai.upload_file(filepath)
        
        prompt = f"""Audit this document based on these criteria:
        {audit_criteria}
        
        Provide a detailed audit report with:
        1. Issues found
        2. Severity levels
        3. Recommendations
        """
        
        response = self.model.generate_content([uploaded_file, prompt])
        return response.text

# Usage
auditor = GeminiAuditTool(api_key="your-gemini-api-key")

# Audit a CSV
result = auditor.audit_csv(
    "expenses.csv",
    """
    - Check for duplicate entries
    - Verify all amounts are positive
    - Flag any expenses over $10,000
    - Check for missing required fields
    """
)

print(result)

# Audit a PDF
pdf_result = auditor.audit_pdf(
    "financial_report.pdf",
    """
    - Verify all required sections are present
    - Check for mathematical errors
    - Flag any compliance issues
    """
)

print(pdf_result)