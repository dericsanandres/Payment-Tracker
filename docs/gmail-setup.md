# Gmail Setup

## Enable Gmail App Password

1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Navigate to **Security** → **2-Step Verification**
3. Enable 2-Step Verification if not already enabled
4. Go to **App passwords**
5. Select app: **Mail**
6. Select device: **Other (custom name)**
7. Enter name: **Payment Tracker**
8. Copy the generated 16-character password

## IMAP Access

Ensure IMAP is enabled:
1. Go to Gmail Settings
2. Click **Forwarding and POP/IMAP** tab
3. Enable **IMAP access**
4. Save changes

## Configuration

Use the app password as `GMAIL_APP_PASSWORD` environment variable:

```bash
export GMAIL_APP_PASSWORD="your-16-char-app-password"
```

**Note**: Use the app password, not your regular Gmail password.
