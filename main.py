"""
Payment Tracker - Cloud Function Entry Point
"""
import functions_framework
import os
import json
from src.logger import get_logger
from src.paytment_extractor import PaymentExtractor
from src.sheets_client import SheetsClient

logger = get_logger(__name__)

# Configuration from environment (populated by Secret Manager)
CONFIG = {
    'gmail_username': 'dercsanandres@gmail.com',
    'gmail_password': os.getenv('GMAIL_APP_PASSWORD'),
    'google_credentials': os.getenv('GOOGLE_SERVICE_ACCOUNT_JSON'),
    'spreadsheet_id': os.getenv('GOOGLE_SPREADSHEET_ID'),
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
        
        # Initialize Google Sheets client and setup spreadsheet
        logger.info("Initializing Google Sheets client")
        sheets_client = SheetsClient(
            credentials_json=CONFIG['google_credentials'],
            spreadsheet_id=CONFIG['spreadsheet_id']
        )
        
        # Ensure spreadsheet exists and has correct schema
        logger.info("Verifying Google Sheets setup")
        sheets_client.ensure_spreadsheet_setup()
        
        # Create payment records
        logger.info(f"Creating {len(payments)} payment records in Google Sheets")
        result = sheets_client.create_payment_records(payments)
        
        logger.info("Payment processing completed successfully")
        
        return {
            "status": "success",
            "payments_processed": len(payments),
            "sheets_result": result,
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

@functions_framework.http
def health_check(request):
    """Health check endpoint."""
    logger.info("Health check requested")
    return {"status": "healthy", "service": "payment-extractor"}

if __name__ == "__main__":
    # For local testing
    import functions_framework
    logger.info("Starting local development server")
    functions_framework._run_flask_app(payment_extractor, debug=True)