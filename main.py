"""
Payment Tracker - Cloud Function Entry Point
"""
import functions_framework
import os
import json
from src.logger import get_logger
from src.paytment_extractor import PaymentExtractor
from src.logger import get_logger
from src.notion_client import NotionClient

logger = get_logger(__name__)

# Configuration from environment (populated by Secret Manager)
CONFIG = {
    'gmail_username': 'dercsanandres@gmail.com',
    'gmail_password': os.getenv('GMAIL_APP_PASSWORD'),
    'notion_token': os.getenv('NOTION_TOKEN'),
    'notion_db_id': os.getenv('NOTION_DATABASE_ID'),
    'days_to_fetch': 600
}

@functions_framework.http
def payment_extractor(request):
    """Main payment extraction function."""
    try:
        logger.info("Payment extraction started")
        
        # Parse request
        request_json = request.get_json(silent=True) or {}
        is_test = request_json.get('test', False)
        
        if is_test:
            logger.info("Test request received")
            config_status = {k: bool(v) for k, v in CONFIG.items()}
            logger.info(f"Configuration status: {config_status}")
            return {
                "status": "healthy",
                "message": "Payment extractor is running",
                "config_loaded": all(CONFIG.values())
            }
        
        # Validate configuration
        missing_config = [k for k, v in CONFIG.items() if not v]
        if missing_config:
            error_msg = f"Missing configuration: {missing_config}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        logger.info("Configuration validated successfully")
        
        # Extract payments
        logger.info("Initializing payment extractor")
        extractor = PaymentExtractor(
            gmail_username=CONFIG['gmail_username'],
            gmail_password=CONFIG['gmail_password'],
            days_back=CONFIG['days_to_fetch']
        )
        
        payments = extractor.extract_all_payments()
        logger.info(f"Payment extraction completed. Found {len(payments)} payments")
        
        if not payments:
            logger.info("No new payments to process")
            return {
                "status": "success",
                "message": "No new payments found",
                "payments_processed": 0
            }
        
        # Initialize Notion client and setup database
        logger.info("Initializing Notion client")
        notion_client = NotionClient(
            token=CONFIG['notion_token'],
            database_id=CONFIG['notion_db_id']
        )
        
        # Ensure database exists and has correct schema
        logger.info("Verifying Notion database setup")
        notion_client.ensure_database_setup()
        
        # Create payment records
        logger.info(f"Creating {len(payments)} payment records in Notion")
        result = notion_client.create_payment_records(payments)
        
        logger.info("Payment processing completed successfully")
        
        return {
            "status": "success",
            "payments_processed": len(payments),
            "notion_result": result,
            "summary": {
                "services": list(set(p.get('service') for p in payments)),
                "total_amount": sum(float(p.get('amount', 0)) for p in payments),
                "currencies": list(set(p.get('currency') for p in payments))
            }
        }
        
    except Exception as e:
        error_msg = f"Payment extraction failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"status": "error", "message": error_msg}, 500

# For Cloud Run compatibility
from flask import Flask, request as flask_request
app = Flask(__name__)

@app.route('/', methods=['POST', 'GET'])
def main_handler():
    return payment_extractor(flask_request)

@app.route('/health', methods=['GET'])
def health_check():
    logger.info("Health check requested")
    return {"status": "healthy", "service": "payment-extractor"}

if __name__ == "__main__":
    logger.info("Starting local development server")
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 8080)))