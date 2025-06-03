# Payment Tracker

Automated payment extraction from Gmail to Notion database using Google Cloud Functions.

## Overview

This tool monitors your Gmail inbox for payment notifications from various services (Wise, PayPal, Remitly, Bill.com) and automatically creates organized records in a Notion database.

## Features

- **Automated Email Processing**: Scans Gmail for payment emails from configured services
- **Duplicate Detection**: Prevents duplicate entries using message IDs
- **Notion Integration**: Auto-creates structured payment records
- **Cloud Deployment**: Runs as Google Cloud Function with configurable scheduling

## Quick Start

### Prerequisites

- Gmail account with app password enabled
- Notion workspace with API token
- Google Cloud account for deployment

### Environment Variables

Required environment variables:

```
GMAIL_APP_PASSWORD=your_gmail_app_password
NOTION_TOKEN=your_notion_integration_token
NOTION_DATABASE_ID=your_notion_database_id
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

### Database Schema

The Notion database will be auto-created with these properties:
- Sender (title)
- Service (select)
- Amount (number)
- Currency (select)
- Date (date)
- Subject (text)
- Message ID (text)
- Additional metadata fields

## API Endpoints

- `POST /` - Trigger payment extraction
- `GET /health` - Health check
- `POST /` with `{"test": true}` - Test configuration

## Processing Logic

1. Connects to Gmail via IMAP
2. Searches for emails from configured services (last 600 days)
3. Extracts payment data using regex patterns
4. Checks for duplicates in Notion database
5. Creates new payment records

## Monitoring

Check logs in Google Cloud Console for:
- Extraction summaries
- Error details
- Duplicate detection results
