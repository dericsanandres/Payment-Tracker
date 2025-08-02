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