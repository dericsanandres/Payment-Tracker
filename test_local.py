#!/usr/bin/env python3
"""
Local Test Script for Payment Tracker
Uses local credentials file instead of environment variables
"""
import os
import json
import sys
from datetime import datetime

# Add src to path for imports
sys.path.append('src')

from logger import get_logger
from paytment_extractor import PaymentExtractor
from sheets_client import SheetsClient

logger = get_logger(__name__)

def load_local_config():
    """Load configuration from local files and environment."""
    config = {}
    
    # Gmail credentials from environment
    config['gmail_username'] = 'dercsanandres@gmail.com'
    config['gmail_password'] = os.getenv('GMAIL_APP_PASSWORD')
    if not config['gmail_password']:
        raise ValueError("GMAIL_APP_PASSWORD environment variable required")
    
    # Google Service Account from file
    service_account_path = 'credentials/service_account.json'
    if not os.path.exists(service_account_path):
        raise FileNotFoundError(f"Service account file not found: {service_account_path}")
    
    with open(service_account_path, 'r') as f:
        config['google_credentials'] = json.dumps(json.load(f))
    
    # Spreadsheet ID from environment
    config['spreadsheet_id'] = os.getenv('GOOGLE_SPREADSHEET_ID')
    if not config['spreadsheet_id']:
        raise ValueError("GOOGLE_SPREADSHEET_ID environment variable required")
    
    config['days_to_fetch'] = 30
    
    return config

def test_configuration():
    """Test that all configuration is properly loaded."""
    try:
        config = load_local_config()
        logger.info("Configuration test passed")
        
        # Test Google Sheets connection
        sheets_client = SheetsClient(
            credentials_json=config['google_credentials'],
            spreadsheet_id=config['spreadsheet_id']
        )
        
        # Get spreadsheet info to verify connection
        info = sheets_client.get_spreadsheet_info()
        logger.info(f"Connected to spreadsheet: {info['title']} ({info['url']})")
        
        return True, config
        
    except Exception as e:
        logger.error(f"Configuration test failed: {e}")
        return False, None

def run_payment_extraction(test_mode=False, test_metrics=False):
    """Run the payment extraction process."""
    try:
        logger.info("=== Payment Tracker Local Test ===")
        
        # Test configuration
        logger.info("Testing configuration...")
        config_ok, config = test_configuration()
        if not config_ok:
            return {"status": "error", "message": "Configuration test failed"}
        
        if test_mode:
            logger.info("Test mode - configuration verified successfully")
            return {
                "status": "success",
                "message": "Local test configuration verified",
                "test_mode": True
            }
        
        if test_metrics:
            logger.info("Testing metrics functionality...")
            sheets_client = SheetsClient(
                credentials_json=config['google_credentials'],
                spreadsheet_id=config['spreadsheet_id']
            )
            sheets_client.ensure_spreadsheet_setup()
            metrics_result = sheets_client.update_metrics()
            
            return {
                "status": "success",
                "message": "Metrics test completed",
                "metrics_result": metrics_result,
                "test_metrics": True
            }
        
        # Extract payments
        logger.info("Initializing payment extractor...")
        extractor = PaymentExtractor(
            gmail_username=config['gmail_username'],
            gmail_password=config['gmail_password'],
            days_back=config['days_to_fetch']
        )
        
        payments = extractor.extract_all_payments()
        logger.info(f"Extracted {len(payments)} payments")
        
        if not payments:
            logger.info("No new payments found")
            return {
                "status": "success",
                "message": "No new payments to process",
                "payments_processed": 0
            }
        
        # Initialize Google Sheets client
        logger.info("Initializing Google Sheets client...")
        sheets_client = SheetsClient(
            credentials_json=config['google_credentials'],
            spreadsheet_id=config['spreadsheet_id']
        )
        
        # Setup spreadsheet
        logger.info("Setting up spreadsheet...")
        sheets_client.ensure_spreadsheet_setup()
        
        # Create payment records
        logger.info(f"Creating {len(payments)} payment records...")
        result = sheets_client.create_payment_records(payments)
        
        # Update metrics after processing payments
        logger.info("Updating metrics...")
        metrics_result = sheets_client.update_metrics()
        
        logger.info("Payment processing completed successfully")
        
        return {
            "status": "success",
            "payments_processed": len(payments),
            "sheets_result": result,
            "metrics_result": metrics_result,
            "summary": {
                "services": list(set(p.get('service') for p in payments)),
                "total_amount": sum(float(p.get('amount', 0)) for p in payments),
                "currencies": list(set(p.get('currency') for p in payments))
            }
        }
        
    except Exception as e:
        error_msg = f"Payment extraction failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"status": "error", "message": error_msg}

def main():
    """Main function with command line options."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Local Payment Tracker Test')
    parser.add_argument('--test', action='store_true', 
                       help='Test configuration only (no email processing)')
    parser.add_argument('--metrics', action='store_true',
                       help='Test metrics functionality only (no email processing)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run the extraction
    result = run_payment_extraction(test_mode=args.test, test_metrics=args.metrics)
    
    # Print results
    print(f"\n=== Results ===")
    print(f"Status: {result['status']}")
    if 'message' in result:
        print(f"Message: {result['message']}")
    
    if result['status'] == 'success':
        if args.metrics or 'metrics_result' in result:
            metrics = result.get('metrics_result', {})
            print(f"Metrics sheet created: {metrics.get('metrics_sheet_created', False)}")
            print(f"Total payments: {metrics.get('total_payments', 0)}")
            print(f"Total amount: {metrics.get('total_amount', 0)}")
            print(f"Average amount: {metrics.get('average_amount', 0):.2f}")
            print(f"Service breakdown: {metrics.get('service_breakdown', {})}")
        
        if not args.test and not args.metrics:
            if 'payments_processed' in result:
                print(f"Payments processed: {result['payments_processed']}")
            if 'sheets_result' in result:
                sheets_result = result['sheets_result']
                print(f"Created: {sheets_result.get('created', 0)}")
                print(f"Duplicates: {sheets_result.get('duplicates', 0)}")
                print(f"Errors: {sheets_result.get('errors', 0)}")
            if 'summary' in result:
                summary = result['summary']
                print(f"Services: {', '.join(summary.get('services', []))}")
                print(f"Total amount: {summary.get('total_amount', 0)}")
                print(f"Currencies: {', '.join(summary.get('currencies', []))}")
    
    return 0 if result['status'] == 'success' else 1

if __name__ == "__main__":
    exit(main())