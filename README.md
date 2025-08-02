# Payment Tracker

Automated payment extraction from Gmail to Google Sheets using Google Cloud Functions.

## Overview

This tool monitors your Gmail inbox for payment notifications from various services (Wise, PayPal, Remitly, Bill.com) and automatically creates organized records in a Google Sheets spreadsheet with comprehensive analytics.

## Features

- **Automated Email Processing**: Scans Gmail for payment emails from configured services
- **Duplicate Detection**: Prevents duplicate entries using message IDs
- **Google Sheets Integration**: Auto-creates structured payment records with metrics
- **Real-time Analytics**: Automatic metrics calculations with Excel formulas
- **Cloud Deployment**: Runs as Google Cloud Function with configurable scheduling

## Quick Start

### Prerequisites

- Gmail account with app password enabled
- Google Sheets spreadsheet with service account access
- Google Cloud account for deployment

### Environment Variables

Required environment variables:

```
GMAIL_APP_PASSWORD=your_gmail_app_password
GOOGLE_SERVICE_ACCOUNT_JSON=your_service_account_json
GOOGLE_SPREADSHEET_ID=your_google_spreadsheet_id
```

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables
3. Run locally:
```bash
python main.py
```

### Deployment

Deploy to Google Cloud Functions using the provided GitHub Actions workflow in `.github/workflows/deploy.yml`.

## Configuration

### Supported Payment Services

- **Wise**: `noreply@wise.com`
- **PayPal**: `service@paypal.com`
- **Remitly**: `no-reply@remitly.com`
- **Bill.com**: `account-services@hq.bill.com`

### Spreadsheet Structure

The Google Sheets spreadsheet will have two sheets:
**Data Sheet:**
- Date (formatted as "2025, Aug 03")
- Service (Wise, Billcom, PayPal, Remitly)
- Sender (extracted from email)
- Amount (with currency, e.g., "6600 PHP")
- Message ID (for duplicate detection)

**Metrics Sheet:**
- Summary metrics (total payments, monthly/yearly counts)
- Service breakdown (count, totals, averages per service)
- Monthly trends (last 6 months analysis)
- All metrics use Excel formulas for real-time updates

## API Endpoints

- `POST /` - Trigger payment extraction
- `GET /health` - Health check
- `POST /` with `{"test": true}` - Test configuration

## Processing Logic

1. Connects to Gmail via IMAP
2. Searches for emails from configured services (last 600 days)
3. Extracts payment data using regex patterns (including HTML email support)
4. Checks for duplicates using Message IDs in Google Sheets
5. Creates new payment records in Data sheet
6. Updates metrics sheet with real-time analytics

## Monitoring

Check logs in Google Cloud Console for:
- Extraction summaries
- Error details
- Duplicate detection results
