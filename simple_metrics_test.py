#!/usr/bin/env python3
"""
Simple Metrics Test - Batch Update Version
"""
import os
import json
import sys

# Add src to path for imports
sys.path.append('src')

from logger import get_logger
from sheets_client import SheetsClient

logger = get_logger(__name__)

def create_simple_metrics(sheets_client):
    """Create a simple metrics sheet with minimal API calls."""
    try:
        spreadsheet = sheets_client.gc.open_by_key(sheets_client.spreadsheet_id)
        
        # Check if metrics sheet already exists
        sheet_names = [worksheet.title for worksheet in spreadsheet.worksheets()]
        if "SimpleMetrics" not in sheet_names:
            logger.info("Creating SimpleMetrics sheet")
            metrics_sheet = spreadsheet.add_worksheet(title="SimpleMetrics", rows=50, cols=6)
        else:
            logger.info("SimpleMetrics sheet already exists")
            metrics_sheet = spreadsheet.worksheet("SimpleMetrics")
        
        # Create all data as batch update
        data = [
            ["Payment Analytics", "", "", "", "", ""],
            ["", "", "", "", "", ""],
            ["SUMMARY METRICS", "", "", "", "", ""],
            ["", "", "", "", "", ""],
            ["Total Payments:", "=COUNTA(Data!E4:E)", "", "Total Amount:", "=SUMPRODUCT(VALUE(LEFT(Data!D4:D,FIND(\" \",Data!D4:D)-1)))", ""],
            ["This Month:", "=COUNTIFS(Data!A4:A,\">=\"&DATE(YEAR(TODAY()),MONTH(TODAY()),1))", "", "Average:", "=AVERAGE(VALUE(LEFT(Data!D4:D,FIND(\" \",Data!D4:D)-1)))", ""],
            ["", "", "", "", "", ""],
            ["SERVICE BREAKDOWN", "", "", "", "", ""],
            ["", "", "", "", "", ""],
            ["Service", "Count", "Total Amount", "", "", ""],
            ["Wise", "=COUNTIF(Data!B4:B,\"Wise\")", "=SUMPRODUCT((Data!B4:B=\"Wise\")*(VALUE(LEFT(Data!D4:D,FIND(\" \",Data!D4:D)-1))))", "", "", ""],
            ["Billcom", "=COUNTIF(Data!B4:B,\"Billcom\")", "=SUMPRODUCT((Data!B4:B=\"Billcom\")*(VALUE(LEFT(Data!D4:D,FIND(\" \",Data!D4:D)-1))))", "", "", ""],
        ]
        
        # Single batch update
        metrics_sheet.clear()
        metrics_sheet.update("A1:F12", data)
        
        logger.info("Simple metrics sheet created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create simple metrics: {e}")
        return False

def main():
    try:
        # Load configuration
        service_account_path = 'credentials/service_account.json'
        with open(service_account_path, 'r') as f:
            google_credentials = json.dumps(json.load(f))
        
        spreadsheet_id = os.getenv('GOOGLE_SPREADSHEET_ID')
        
        # Initialize Google Sheets client
        sheets_client = SheetsClient(
            credentials_json=google_credentials,
            spreadsheet_id=spreadsheet_id
        )
        
        # Create simple metrics
        success = create_simple_metrics(sheets_client)
        print(f"Simple metrics creation: {'SUCCESS' if success else 'FAILED'}")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())