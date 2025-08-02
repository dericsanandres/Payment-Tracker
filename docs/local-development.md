# Local Development Setup

This guide explains how to run the Payment Tracker locally for testing and development.

## Prerequisites

- Python 3.9+
- Gmail account with app password
- Google Cloud service account with Sheets API access
- Google Spreadsheet

## Quick Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Set Up Credentials

#### Option A: Using Local Files (Recommended for Development)

1. **Place service account file**:
   ```bash
   # Download service account JSON from Google Cloud Console
   # Save it as: credentials/service_account.json
   ```

2. **Set environment variables**:
   ```bash
   export GMAIL_APP_PASSWORD="your_gmail_app_password"
   export GOOGLE_SPREADSHEET_ID="your_spreadsheet_id"
   ```

#### Option B: Using Environment Variables

```bash
export GMAIL_APP_PASSWORD="your_gmail_app_password"
export GOOGLE_SERVICE_ACCOUNT_JSON='{"type":"service_account",...}'
export GOOGLE_SPREADSHEET_ID="your_spreadsheet_id"
```

### 3. Run Local Tests

#### Test Configuration Only
```bash
python test_local.py --test
```

#### Run Full Payment Extraction
```bash
python test_local.py
```

#### Verbose Logging
```bash
python test_local.py --test --verbose
```

## File Structure

```
Payment-Tracker/
├── credentials/
│   ├── service_account.json    # Your Google Cloud service account (gitignored)
│   └── .gitkeep               # Keeps directory in git
├── test_local.py              # Local test script
├── main.py                    # Cloud Function entry point
└── .env                       # Environment variables (gitignored)
```

## Test Script Features

The `test_local.py` script provides:

- **Configuration Testing**: Verify all credentials and connections
- **Local File Support**: Reads service account from `credentials/service_account.json`
- **Full Extraction**: Complete payment extraction and Google Sheets upload
- **Verbose Logging**: Debug information for troubleshooting
- **Error Handling**: Clear error messages for common issues

## Common Commands

```bash
# Test configuration only
python test_local.py --test

# Run with detailed logging
python test_local.py --verbose

# Full extraction (production-like)
python test_local.py

# Run original main.py (uses environment variables)
python main.py
```

## Troubleshooting

### Configuration Issues

1. **Service account file not found**:
   ```
   FileNotFoundError: Service account file not found: credentials/service_account.json
   ```
   - Download service account JSON from Google Cloud Console
   - Save as `credentials/service_account.json`

2. **Missing environment variables**:
   ```
   ValueError: GMAIL_APP_PASSWORD environment variable required
   ```
   - Set required environment variables (see setup section)

3. **Spreadsheet access denied**:
   ```
   gspread.exceptions.APIError: [403] The caller does not have permission
   ```
   - Share spreadsheet with service account email
   - Check service account has Sheets API enabled

### Gmail Connection Issues

1. **Authentication failed**:
   - Verify Gmail app password is correct
   - Ensure 2FA is enabled on Gmail account
   - Generate new app password if needed

2. **IMAP access denied**:
   - Enable IMAP in Gmail settings
   - Check app password permissions

### Google Sheets Issues

1. **Spreadsheet not found**:
   - Verify spreadsheet ID is correct
   - Check spreadsheet is shared with service account

2. **API quota exceeded**:
   - Reduce frequency of testing
   - Check Google Cloud Console quotas

## Development Tips

1. **Use test mode** (`--test`) during development to avoid processing emails
2. **Enable verbose logging** (`--verbose`) for debugging
3. **Keep credentials secure** - they're automatically gitignored
4. **Use separate test spreadsheet** for development

## Security Notes

- Credential files are automatically excluded from git
- Never commit `credentials/service_account.json` to version control
- Use environment variables for sensitive data
- Rotate service account keys regularly

## Next Steps

After local testing works:
1. Set up Google Secret Manager (see `docs/deployment.md`)
2. Deploy to Google Cloud Functions
3. Configure Cloud Scheduler for automation