# Payment Tracker

Automatically extracts payment notifications from Gmail and logs them to Notion.

## Setup

1. **Gmail App Password**: Generate at [Google Account Security](https://myaccount.google.com/security)
2. **Notion Integration**: Create at [Notion Integrations](https://www.notion.so/my-integrations)
3. **Environment Variables**:
   - `GMAIL_APP_PASSWORD`
   - `NOTION_TOKEN` 
   - `NOTION_DATABASE_ID`

## Supported Services

- Wise (`noreply@wise.com`)
- PayPal (`service@paypal.com`)
- Remitly (`no-reply@remitly.com`)
- Bill.com (`bill.com`)

## Deployment

**Google Cloud Functions:**
```bash
gcloud functions deploy payment-extractor \
  --runtime python39 \
  --trigger-http \
  --allow-unauthenticated
```

**Local Development:**
```bash
pip install -r src/requirements.txt
python src/main.py
```

## Usage

- **Manual**: POST to function URL
- **Scheduled**: Runs 1st and 15th of each month at 9 AM EST
- **Test**: POST `{"test": true}` for health check

## Features

- Extracts amount, currency, sender from emails
- Creates Notion database with proper schema
- Handles multiple currencies (USD, PHP, EUR, GBP, CAD)
- Comprehensive logging
- Error handling and validation