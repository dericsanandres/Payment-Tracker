"""
Notion client with database management and schema validation.
"""
from notion_client import Client
from typing import List, Dict, Any, Optional
import time
from src.logger import get_logger

logger = get_logger(__name__)

class NotionClient:
    """Notion client with automatic database setup and management."""
    
    def __init__(self, token: str, database_id: Optional[str] = None):
        self.client = Client(auth=token)
        self.database_id = database_id
        self.required_properties = self._get_required_schema()
        
        logger.info("NotionClient initialized")
    
    def _get_required_schema(self) -> Dict[str, Dict]:
        """Define the required database schema for payment tracking."""
        return {
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
            "Sender": {
                "type": "title",
                "title": {}
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
    
    def create_payment_records(self, payments: List[Dict]) -> Dict[str, Any]:
        """Create payment records in the Notion database."""
        logger.info(f"Creating {len(payments)} payment records")
        
        created_count = 0
        failed_count = 0
        errors = []
        
        for payment in payments:
            try:
                self._create_single_payment_record(payment)
                created_count += 1
                
                # Add small delay to respect rate limits
                time.sleep(0.1)
                
            except Exception as e:
                failed_count += 1
                error_msg = f"Failed to create record for {payment.get('sender', 'unknown')}: {str(e)}"
                logger.error(error_msg)
                errors.append(error_msg)
        
        result = {
            "created": created_count,
            "failed": failed_count,
            "errors": errors
        }
        
        logger.info(f"Payment record creation completed: {created_count} created, {failed_count} failed")
        return result
    
    def _create_single_payment_record(self, payment: Dict) -> None:
        """Create a single payment record in Notion."""
        try:
            # Convert payment data to Notion properties format
            properties = {
                "Service": {"select": {"name": payment.get("service", "Unknown")}},
                "Sender": {"title": [{"text": {"content": payment.get("sender", "Unknown")}}]},
                "Amount": {"number": float(payment.get("amount", 0))},
                "Currency": {"select": {"name": payment.get("currency", "USD")}},
                "Subject": {"rich_text": [{"text": {"content": payment.get("subject", "")}}]},
                "Days Ago": {"rich_text": [{"text": {"content": payment.get("days_ago", "Unknown")}}]}
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
            
            logger.debug(f"Created record for {payment.get('sender')} - {payment.get('amount')} {payment.get('currency')}")
            
        except Exception as e:
            logger.error(f"Failed to create single record: {str(e)}")
            raise