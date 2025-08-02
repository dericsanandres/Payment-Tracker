"""
Google Sheets Client for Payment Tracker
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from email.utils import parsedate_to_datetime
import gspread
from google.oauth2.service_account import Credentials
from logger import get_logger

logger = get_logger(__name__)

class SheetsClient:
    """Google Sheets client for managing payment records."""
    
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    
    HEADERS = [
        'Date',
        'Service', 
        'Sender',
        'Amount',
        'Message ID'
    ]
    
    def __init__(self, credentials_json: str, spreadsheet_id: str):
        """
        Initialize Google Sheets client.
        
        Args:
            credentials_json: Service account credentials as JSON string
            spreadsheet_id: Google Sheets spreadsheet ID
        """
        self.spreadsheet_id = spreadsheet_id
        self.gc = None
        self.sheet = None
        
        try:
            # Parse credentials
            creds_dict = json.loads(credentials_json)
            credentials = Credentials.from_service_account_info(
                creds_dict, scopes=self.SCOPES
            )
            
            # Initialize gspread client
            self.gc = gspread.authorize(credentials)
            logger.info("Google Sheets client initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Google Sheets client: {e}")
            raise
    
    def ensure_spreadsheet_setup(self) -> None:
        """Ensure spreadsheet exists and has correct headers."""
        try:
            # Open spreadsheet
            self.sheet = self.gc.open_by_key(self.spreadsheet_id).sheet1
            logger.info(f"Opened spreadsheet: {self.spreadsheet_id}")
            
            # Ensure sheet is named 'Data' for metrics references
            self._ensure_sheet_named_data()
            
            # Check if headers exist at row 3
            try:
                existing_headers = self.sheet.row_values(3)
                if not existing_headers or existing_headers != self.HEADERS:
                    logger.info("Setting up spreadsheet structure")
                    self.sheet.clear()
                    
                    # Row 1: Last Run tracking (same format as payment dates)
                    current_time = datetime.now().strftime('%Y, %b %d')
                    self.sheet.update('A1', f'Last Run: {current_time}')
                    
                    # Row 2: Empty
                    
                    # Row 3: Headers
                    self.sheet.append_row([], table_range='A3')  # Start at row 3
                    self.sheet.update('A3:E3', [self.HEADERS])
                    
                    logger.info("Spreadsheet structure and headers added")
                else:
                    # Update last run time (same format as payment dates)
                    current_time = datetime.now().strftime('%Y, %b %d')
                    self.sheet.update('A1', f'Last Run: {current_time}')
                    logger.info("Spreadsheet headers already configured, updated last run time")
            except Exception as e:
                logger.warning(f"Could not read headers, setting up new structure: {e}")
                self.sheet.clear()
                
                # Row 1: Last Run tracking (same format as payment dates)
                current_time = datetime.now().strftime('%Y, %b %d')
                self.sheet.update('A1', f'Last Run: {current_time}')
                
                # Row 2: Empty
                
                # Row 3: Headers
                self.sheet.update('A3:E3', [self.HEADERS])
                
        except Exception as e:
            logger.error(f"Failed to setup spreadsheet: {str(e)}", exc_info=True)
            raise
    
    def get_existing_message_ids(self) -> set:
        """Get all existing message IDs to prevent duplicates."""
        try:
            if not self.sheet:
                self.ensure_spreadsheet_setup()
            
            # Get all records starting from row 4 (data rows after header at row 3)
            try:
                records = self.sheet.get_all_records(head=3)  # Headers are at row 3
                
                # Extract message IDs (column E, index 4)
                message_ids = {record.get('Message ID', '') for record in records}
                message_ids.discard('')  # Remove empty strings
                
                logger.info(f"Found {len(message_ids)} existing message IDs")
                return message_ids
            except Exception as e:
                logger.warning(f"Could not read existing records: {e}")
                return set()
            
        except Exception as e:
            logger.error(f"Failed to get existing message IDs: {e}")
            return set()
    
    def create_payment_records(self, payments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create payment records in Google Sheets.
        
        Args:
            payments: List of payment dictionaries
            
        Returns:
            Dictionary with creation results
        """
        try:
            if not payments:
                return {"created": 0, "duplicates": 0, "errors": 0}
            
            if not self.sheet:
                self.ensure_spreadsheet_setup()
            
            # Get existing message IDs to check for duplicates
            existing_ids = self.get_existing_message_ids()
            
            created_count = 0
            duplicate_count = 0
            error_count = 0
            
            # Sort payments by date (newest first)
            def parse_date_for_sorting(payment):
                try:
                    date_str = payment.get('date', '')
                    if date_str:
                        if isinstance(date_str, str):
                            # Try RFC format first (email format)
                            try:
                                date_obj = parsedate_to_datetime(date_str)
                            except:
                                # Fallback to ISO format
                                date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        else:
                            date_obj = date_str
                        return date_obj
                    return datetime.min
                except Exception:
                    return datetime.min
            
            sorted_payments = sorted(payments, key=parse_date_for_sorting, reverse=True)
            
            # Prepare rows to batch insert
            rows_to_insert = []
            
            for payment in sorted_payments:
                try:
                    message_id = payment.get('message_id', '')
                    
                    # Check for duplicates
                    if message_id in existing_ids:
                        logger.info(f"Skipping duplicate payment: {message_id}")
                        duplicate_count += 1
                        continue
                    
                    # Parse date and format as "2025, Aug 13"
                    date_str = payment.get('date', '')
                    if date_str:
                        try:
                            # Convert to datetime and format as "2025, Aug 13"
                            if isinstance(date_str, str):
                                # Try RFC format first (email format)
                                try:
                                    date_obj = parsedate_to_datetime(date_str)
                                except:
                                    # Fallback to ISO format
                                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                            else:
                                date_obj = date_str
                            formatted_date = date_obj.strftime('%Y, %b %d')
                        except Exception as e:
                            logger.warning(f"Date parsing error: {e}, using original: {date_str}")
                            formatted_date = str(date_str)
                    else:
                        formatted_date = ''
                    
                    # Prepare row data (combined amount + currency, removed Created At)
                    amount = payment.get('amount', '')
                    currency = payment.get('currency', 'PHP')
                    amount_with_currency = f"{amount} {currency}" if amount else ""
                    
                    row = [
                        formatted_date,                           # Date
                        payment.get('service', ''),              # Service
                        payment.get('sender', ''),               # Sender
                        amount_with_currency,                     # Amount (with currency)
                        message_id,                              # Message ID
                    ]
                    
                    rows_to_insert.append(row)
                    existing_ids.add(message_id)  # Add to prevent duplicates in this batch
                    
                except Exception as e:
                    logger.error(f"Error processing payment record: {e}")
                    error_count += 1
            
            # Batch insert all rows (after headers at row 3)
            if rows_to_insert:
                self.sheet.append_rows(rows_to_insert, table_range='A4')  # Start data at row 4
                created_count = len(rows_to_insert)
                logger.info(f"Successfully created {created_count} payment records")
            
            result = {
                "created": created_count,
                "duplicates": duplicate_count,
                "errors": error_count,
                "total_processed": len(payments)
            }
            
            logger.info(f"Payment records creation result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Failed to create payment records: {e}")
            raise
    
    def get_spreadsheet_info(self) -> Dict[str, Any]:
        """Get basic spreadsheet information."""
        try:
            if not self.sheet:
                self.ensure_spreadsheet_setup()
            
            spreadsheet = self.gc.open_by_key(self.spreadsheet_id)
            
            return {
                "title": spreadsheet.title,
                "id": self.spreadsheet_id,
                "url": f"https://docs.google.com/spreadsheets/d/{self.spreadsheet_id}",
                "sheet_title": self.sheet.title,
                "row_count": self.sheet.row_count,
                "col_count": self.sheet.col_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get spreadsheet info: {str(e)}", exc_info=True)
            raise
    
    def create_metrics_sheet(self) -> None:
        """Create a separate sheet for metrics and analytics."""
        try:
            spreadsheet = self.gc.open_by_key(self.spreadsheet_id)
            
            # Check if metrics sheet already exists
            sheet_names = [worksheet.title for worksheet in spreadsheet.worksheets()]
            if "Metrics" not in sheet_names:
                logger.info("Creating Metrics sheet")
                metrics_sheet = spreadsheet.add_worksheet(title="Metrics", rows=100, cols=10)
            else:
                logger.info("Metrics sheet already exists")
                metrics_sheet = spreadsheet.worksheet("Metrics")
            
            # Set up metrics sheet structure
            self._setup_metrics_sheet(metrics_sheet)
            
        except Exception as e:
            logger.error(f"Failed to create metrics sheet: {str(e)}", exc_info=True)
            raise
    
    def _setup_metrics_sheet(self, metrics_sheet) -> None:
        """Set up the metrics sheet with headers and formulas."""
        try:
            logger.info("Setting up metrics sheet structure")
            
            # Clear existing content
            metrics_sheet.clear()
            
            # Headers and layout
            current_date = datetime.now().strftime('%Y, %b %d')
            
            # Row 1: Title
            metrics_sheet.update('A1', f'Payment Analytics - Updated: {current_date}')
            
            # Row 3: Summary Metrics Headers
            metrics_sheet.update('A3:F3', [['SUMMARY METRICS', '', '', '', '', '']])
            
            # Row 4-6: Metric labels and formulas (insert individually to ensure formula recognition)
            metrics_sheet.update('A5', 'Total Payments:')
            metrics_sheet.update('B5', '=COUNTA(Data!E4:E)')
            metrics_sheet.update('D5', 'Total Amount (PHP):')
            metrics_sheet.update('E5', '=SUMPRODUCT(VALUE(LEFT(Data!D4:D,FIND(" ",Data!D4:D)-1)))')
            
            metrics_sheet.update('A6', 'This Month:')
            metrics_sheet.update('B6', '=COUNTIFS(Data!A4:A,">="&DATE(YEAR(TODAY()),MONTH(TODAY()),1),Data!A4:A,"<"&DATE(YEAR(TODAY()),MONTH(TODAY())+1,1))')
            metrics_sheet.update('D6', 'Avg Payment:')
            metrics_sheet.update('E6', '=AVERAGE(VALUE(LEFT(Data!D4:D,FIND(" ",Data!D4:D)-1)))')
            
            metrics_sheet.update('A7', 'This Year:')
            metrics_sheet.update('B7', '=COUNTIFS(Data!A4:A,">="&DATE(YEAR(TODAY()),1,1),Data!A4:A,"<"&DATE(YEAR(TODAY())+1,1,1))')
            metrics_sheet.update('D7', 'Last Payment:')
            metrics_sheet.update('E7', '=MAX(Data!A4:A)')
            
            # Row 9: Service Breakdown
            metrics_sheet.update('A9:F9', [['SERVICE BREAKDOWN', '', '', '', '', '']])
            
            # Service breakdown headers
            metrics_sheet.update('A11:F11', [['Service', 'Count', 'Total Amount', 'Avg Amount', 'Last Payment', '']])
            
            # Service breakdown data - insert each row individually
            services = [
                ('Wise', 12),
                ('Billcom', 13), 
                ('PayPal', 14),
                ('Remitly', 15)
            ]
            
            for service_name, row_num in services:
                metrics_sheet.update(f'A{row_num}', service_name)
                metrics_sheet.update(f'B{row_num}', f'=COUNTIF(Data!B4:B,"{service_name}")')
                metrics_sheet.update(f'C{row_num}', f'=SUMPRODUCT((Data!B4:B="{service_name}")*(VALUE(LEFT(Data!D4:D,FIND(" ",Data!D4:D)-1))))')
                metrics_sheet.update(f'D{row_num}', f'=AVERAGEIF(Data!B4:B,"{service_name}",VALUE(LEFT(Data!D4:D,FIND(" ",Data!D4:D)-1)))')
                metrics_sheet.update(f'E{row_num}', f'=MAXIFS(Data!A4:A,Data!B4:B,"{service_name}")')
            
            # Row 17: Monthly Breakdown
            metrics_sheet.update('A17:F17', [['MONTHLY BREAKDOWN (Last 6 Months)', '', '', '', '', '']])
            
            # Monthly breakdown headers
            metrics_sheet.update('A18:F18', [['Month', 'Count', 'Total Amount', 'Avg Amount', 'Top Service', '']])
            
            # Generate formulas for last 6 months - insert each cell individually
            for i in range(6):
                row_num = 19 + i
                month_offset = i
                
                # Month formula
                metrics_sheet.update(f'A{row_num}', f'=TEXT(DATE(YEAR(TODAY()),MONTH(TODAY())-{month_offset},1),"YYYY, MMM")')
                
                # Count formula
                metrics_sheet.update(f'B{row_num}', f'=COUNTIFS(Data!A4:A,">="&DATE(YEAR(TODAY()),MONTH(TODAY())-{month_offset},1),Data!A4:A,"<"&DATE(YEAR(TODAY()),MONTH(TODAY())-{month_offset}+1,1))')
                
                # Total amount formula
                metrics_sheet.update(f'C{row_num}', f'=SUMPRODUCT((Data!A4:A>=DATE(YEAR(TODAY()),MONTH(TODAY())-{month_offset},1))*(Data!A4:A<DATE(YEAR(TODAY()),MONTH(TODAY())-{month_offset}+1,1))*(VALUE(LEFT(Data!D4:D,FIND(" ",Data!D4:D)-1))))')
                
                # Average formula
                metrics_sheet.update(f'D{row_num}', f'=IF(B{row_num}=0,"",C{row_num}/B{row_num})')
            
            # Format headers
            metrics_sheet.format('A1', {'textFormat': {'bold': True, 'fontSize': 14}})
            metrics_sheet.format('A3:F3', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}})
            metrics_sheet.format('A9:F9', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}})
            metrics_sheet.format('A17:F17', {'textFormat': {'bold': True}, 'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}})
            metrics_sheet.format('A18:F18', {'textFormat': {'bold': True}})
            
            logger.info("Metrics sheet setup completed")
            
        except Exception as e:
            logger.error(f"Failed to setup metrics sheet: {str(e)}", exc_info=True)
            raise
    
    def _ensure_sheet_named_data(self) -> None:
        """Ensure the main sheet is named 'Data' for metrics references."""
        try:
            if self.sheet and self.sheet.title != "Data":
                logger.info(f"Renaming sheet from '{self.sheet.title}' to 'Data'")
                self.sheet.update_title("Data")
                logger.info("Sheet successfully renamed to 'Data'")
            elif self.sheet and self.sheet.title == "Data":
                logger.info("Sheet already named 'Data'")
            
        except Exception as e:
            logger.error(f"Failed to rename sheet to 'Data': {e}")
            raise
    
    def update_metrics(self) -> Dict[str, Any]:
        """Update metrics and return summary information."""
        try:
            # Ensure data sheet is properly named
            self._ensure_sheet_named_data()
            
            # Create/update metrics sheet
            self.create_metrics_sheet()
            
            # Get basic metrics for return
            records = self.sheet.get_all_records(head=3) if self.sheet else []
            
            total_payments = len(records)
            if total_payments > 0:
                amounts = []
                services = []
                for record in records:
                    amount_str = record.get('Amount', '0')
                    try:
                        # Extract numeric part before currency
                        amount = float(amount_str.split(' ')[0].replace(',', ''))
                        amounts.append(amount)
                    except:
                        pass
                    services.append(record.get('Service', 'Unknown'))
                
                total_amount = sum(amounts)
                avg_amount = total_amount / len(amounts) if amounts else 0
                service_counts = {service: services.count(service) for service in set(services)}
            else:
                total_amount = 0
                avg_amount = 0
                service_counts = {}
            
            metrics_summary = {
                "total_payments": total_payments,
                "total_amount": total_amount,
                "average_amount": avg_amount,
                "service_breakdown": service_counts,
                "metrics_sheet_created": True
            }
            
            logger.info(f"Metrics updated: {metrics_summary}")
            return metrics_summary
            
        except Exception as e:
            logger.error(f"Failed to update metrics: {str(e)}", exc_info=True)
            return {"error": str(e), "metrics_sheet_created": False}