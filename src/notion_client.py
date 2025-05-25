"""
Notion client with database management, schema validation, and duplicate detection.
"""
from notion_client import Client
from typing import List, Dict, Any, Optional, Set
import time
from src.logger import get_logger

logger = get_logger(__name__)

class NotionClient:
    """Notion client with automatic database setup, management, and duplicate detection."""
    
    def __init__(self, token: str, database_id: Optional[str] = None):
        self.client = Client(auth=token)
        self.database_id = database_id
        self.required_properties = self._get_required_schema()
        
        logger.info("NotionClient initialized")
    
    def _get_required_schema(self) -> Dict[str, Dict]:
        """Define the required database schema for payment tracking with duplicate detection."""
        return {
            "Sender": {
                "type": "title",
                "title": {}
            },
            "Service": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "Wise", "color": "green"},
                        {"name": "Paypal", "color": "blue"}, 
                        {"name": "Remitly", "color": "orange"},
                        {"name": "Billcom", "color": "purple"}
                    ]
                }
            },
            "Amount": {
                "type": "number",
                "number": {"format": "number"}
            },
            "Currency": {
                "type": "select",
                "select": {
                    "options": [
                        {"name": "USD", "color": "default"},
                        {"name": "PHP", "color": "yellow"},
                        {"name": "EUR", "color": "green"},
                        {"name": "GBP", "color": "blue"},
                        {"name": "CAD", "color": "red"}
                    ]
                }
            },
            "Date": {
                "type": "date",
                "date": {}
            },
            "Subject": {
                "type": "rich_text",
                "rich_text": {}
            },
            "Days Ago": {
                "type": "rich_text", 
                "rich_text": {}
            },
            "Message ID": {
                "type": "rich_text",
                "rich_text": {}
            },
            "From Email": {
                "type": "rich_text",
                "rich_text": {}
            },
            "To Email": {
                "type": "rich_text",
                "rich_text": {}
            },
            "Extraction Timestamp": {
                "type": "rich_text",
                "rich_text": {}
            },
            "Created": {
                "type": "created_time",
                "created_time": {}
            }
        }
    
    def ensure_database_setup(self) -> str:
        """Ensure database exists with correct schema, create if necessary."""
        logger.info("Checking database setup")
        
        if self.database_id:
            # Check if existing database has correct schema
            if self._validate_database_schema():
                logger.info("Database schema validation passed")
                return self.database_id
            else:
                logger.warning("Database schema validation failed, updating schema")
                self._update_database_schema()
                return self.database_id
        else:
            # Create new database
            logger.info("No database ID provided, creating new database")
            self.database_id = self._create_database()
            return self.database_id
    
    def _validate_database_schema(self) -> bool:
        """Validate that the database has the required properties."""
        try:
            logger.debug(f"Validating schema for database {self.database_id}")
            database = self.client.databases.retrieve(database_id=self.database_id)
            existing_properties = database.get("properties", {})
            
            # Check if all required properties exist
            for prop_name, prop_config in self.required_properties.items():
                if prop_name not in existing_properties:
                    logger.warning(f"Missing property: {prop_name}")
                    return False
                
                existing_prop = existing_properties[prop_name]
                if existing_prop.get("type") != prop_config.get("type"):
                    logger.warning(f"Property type mismatch for {prop_name}: expected {prop_config.get('type')}, got {existing_prop.get('type')}")
                    return False
            
            logger.debug("Database schema validation successful")
            return True
            
        except Exception as e:
            logger.error(f"Database validation error: {str(e)}")
            return False
    
    def _update_database_schema(self) -> None:
        """Update database schema with missing properties."""
        try:
            logger.info("Updating database schema")
            
            # Get current properties
            database = self.client.databases.retrieve(database_id=self.database_id)
            existing_properties = database.get("properties", {})
            
            # Add missing properties
            properties_to_add = {}
            for prop_name, prop_config in self.required_properties.items():
                if prop_name not in existing_properties:
                    properties_to_add[prop_name] = prop_config
                    logger.info(f"Adding property: {prop_name}")
            
            if properties_to_add:
                self.client.databases.update(
                    database_id=self.database_id,
                    properties=properties_to_add
                )
                logger.info("Database schema updated successfully")
            else:
                logger.info("No schema updates needed")
                
        except Exception as e:
            logger.error(f"Failed to update database schema: {str(e)}")
            raise
    
    def _create_database(self) -> str:
        """Create a new database with the required schema."""
        try:
            logger.info("Creating new Notion database")
            
            # Create database in the default page (you may need to adjust this)
            database = self.client.databases.create(
                parent={"type": "page_id", "page_id": "your-parent-page-id"},  # Update this
                title=[{"type": "text", "text": {"content": "Payment Tracker"}}],
                properties=self.required_properties
            )
            
            database_id = database["id"]
            logger.info(f"Database created successfully with ID: {database_id}")
            return database_id
            
        except Exception as e:
            logger.error(f"Failed to create database: {str(e)}")
            raise
    
    def _get_existing_message_ids(self) -> Set[str]:
        """Efficiently retrieve all existing message IDs from the database."""
        try:
            logger.info("Fetching existing message IDs for duplicate detection")
            
            existing_ids = set()
            has_more = True
            next_cursor = None
            
            while has_more:
                # Query database with pagination
                query_params = {
                    "database_id": self.database_id,
                    "page_size": 100,  # Maximum page size
                    "filter": {
                        "property": "Message ID",
                        "rich_text": {
                            "is_not_empty": True
                        }
                    }
                }
                
                if next_cursor:
                    query_params["start_cursor"] = next_cursor
                
                response = self.client.databases.query(**query_params)
                
                # Extract message IDs from results
                for page in response.get("results", []):
                    message_id_prop = page.get("properties", {}).get("Message ID", {})
                    rich_text = message_id_prop.get("rich_text", [])
                    if rich_text and len(rich_text) > 0:
                        message_id = rich_text[0].get("text", {}).get("content", "")
                        if message_id:
                            existing_ids.add(message_id)
                
                # Check for more pages
                has_more = response.get("has_more", False)
                next_cursor = response.get("next_cursor")
            
            logger.info(f"Retrieved {len(existing_ids)} existing message IDs")
            return existing_ids
            
        except Exception as e:
            logger.error(f"Error fetching existing message IDs: {str(e)}")
            return set()  # Return empty set on error to allow processing
    
    def create_payment_records(self, payments: List[Dict]) -> Dict[str, Any]:
        """Create payment records in the Notion database with duplicate detection."""
        logger.info(f"Creating payment records with duplicate detection for {len(payments)} payments")
        
        # Get all existing message IDs in one efficient query
        existing_message_ids = self._get_existing_message_ids()
        
        created_count = 0
        skipped_count = 0
        failed_count = 0
        errors = []
        
        for payment in payments:
            try:
                message_id = payment.get('message_id', '')
                
                # Check for duplicate
                if message_id in existing_message_ids:
                    skipped_count += 1
                    logger.info(f"Skipping duplicate payment with message_id: {message_id}")
                    continue
                
                # Create new record
                self._create_single_payment_record(payment)
                created_count += 1
                
                # Add to existing set to prevent duplicates within the same batch
                existing_message_ids.add(message_id)
                
                # Add small delay to respect rate limits
                time.sleep(0.1)
                
            except Exception as e:
                failed_count += 1
                error_msg = f"Failed to create record for {payment.get('sender', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        result = {
            "created": created_count,
            "skipped_duplicates": skipped_count,
            "failed": failed_count,
            "errors": errors
        }
        
        logger.info(f"Payment record creation completed: {created_count} created, {skipped_count} duplicates skipped, {failed_count} failed")
        return result
    
    def _create_single_payment_record(self, payment: Dict) -> None:
        """Create a single payment record in Notion with all available fields."""
        try:
            # Convert payment data to Notion properties format
            properties = {
                "Sender": {"title": [{"text": {"content": payment.get("sender", "Unknown")}}]},
                "Service": {"select": {"name": payment.get("service", "Unknown")}},
                "Amount": {"number": float(payment.get("amount", 0))},
                "Currency": {"select": {"name": payment.get("currency", "USD")}},
                "Subject": {"rich_text": [{"text": {"content": payment.get("subject", "")}}]},
                "Days Ago": {"rich_text": [{"text": {"content": payment.get("days_ago", "Unknown")}}]},
                "Message ID": {"rich_text": [{"text": {"content": payment.get("message_id", "")}}]},
                "From Email": {"rich_text": [{"text": {"content": payment.get("from_email", "")}}]},
                "To Email": {"rich_text": [{"text": {"content": payment.get("to_email", "")}}]},
                "Extraction Timestamp": {"rich_text": [{"text": {"content": payment.get("extraction_timestamp", "")}}]}
            }
            
            # Add date if available
            if payment.get("date"):
                try:
                    from email.utils import parsedate_to_datetime
                    date_obj = parsedate_to_datetime(payment["date"])
                    properties["Date"] = {"date": {"start": date_obj.isoformat()}}
                except Exception:
                    logger.debug(f"Could not parse date: {payment.get('date')}")
            
            # Create the page
            self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            logger.debug(f"Created record for {payment.get('sender')} - {payment.get('amount')} {payment.get('currency')} (ID: {payment.get('message_id')})")
            
        except Exception as e:
            logger.error(f"Failed to create single record: {str(e)}")
            raise