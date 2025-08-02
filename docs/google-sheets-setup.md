# Google Sheets Setup Guide

This guide will help you set up Google Sheets integration for the Payment Tracker.

## Prerequisites

- Google Cloud Platform account
- Google Sheets access

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Note your project ID

## Step 2: Enable Required APIs

1. In the Google Cloud Console, go to "APIs & Services" > "Library"
2. Enable the following APIs:
   - **Google Sheets API**
   - **Google Drive API**

## Step 3: Create Service Account

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service account"
3. Fill in the service account details:
   - Name: `payment-tracker-service`
   - Description: `Service account for Payment Tracker application`
4. Click "Create and Continue"
5. Skip the optional steps and click "Done"

## Step 4: Generate Service Account Key

1. Click on the created service account
2. Go to the "Keys" tab
3. Click "Add Key" > "Create new key"
4. Select "JSON" format
5. Download the JSON file
6. **Keep this file secure** - it contains your credentials

## Step 5: Create Google Spreadsheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new spreadsheet
3. Name it "Payment Tracker" (or your preferred name)
4. Copy the spreadsheet ID from the URL:
   ```
   https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit
   ```

## Step 6: Share Spreadsheet with Service Account

1. In your Google Spreadsheet, click "Share"
2. Add the service account email (found in the JSON file as `client_email`)
3. Give it "Editor" permissions
4. Click "Send"

## Step 7: Configure Environment Variables

1. Open the downloaded JSON credentials file
2. Copy the entire JSON content
3. Set the environment variables:

```bash
# The entire JSON object as a string
GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account","project_id":"your-project",...}'

# The spreadsheet ID from step 5
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here
```

## Step 8: Test the Integration

Run the application with test mode:

```bash
curl -X POST http://localhost:8080 \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```

## Spreadsheet Schema

The application will automatically create the following columns:

| Column | Description |
|--------|-------------|
| Date | Payment date |
| Service | Payment service (Wise, PayPal, etc.) |
| Sender | Email sender |
| Amount | Payment amount |
| Currency | Currency code |
| Subject | Email subject |
| Message ID | Unique email identifier |
| Created At | Record creation timestamp |

## Security Notes

- Never commit the service account JSON file to version control
- Store credentials as environment variables or in secure secret management
- Use least privilege access - only grant necessary permissions
- Regularly rotate service account keys

## Troubleshooting

### Common Issues

1. **Permission denied**: Ensure service account has access to the spreadsheet
2. **API not enabled**: Enable Google Sheets and Drive APIs in Cloud Console
3. **Invalid credentials**: Verify the JSON format and content
4. **Spreadsheet not found**: Check the spreadsheet ID and sharing permissions

### Error Messages

- `gspread.exceptions.APIError`: Usually API access or permission issues
- `gspread.exceptions.SpreadsheetNotFound`: Spreadsheet ID incorrect or not shared
- `ValueError: Invalid JSON`: Check credentials format

## Support

For additional help:
- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [Google Service Accounts Guide](https://cloud.google.com/iam/docs/service-accounts)
- [gspread Documentation](https://docs.gspread.org/)