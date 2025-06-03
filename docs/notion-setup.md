# Notion Setup

## Create Notion Integration

1. Go to [Notion Integrations](https://www.notion.so/my-integrations)
2. Click **New integration**
3. Fill in basic information:
   - Name: Payment Tracker
   - Logo: (optional)
   - Associated workspace: Select your workspace
4. Click **Submit**
5. Copy the **Internal Integration Token**

## Database Setup

The application will automatically create the database schema, but you need to:

1. Create a new page in Notion
2. Add a database to that page
3. Copy the database ID from the URL:
   ```
   https://notion.so/your-workspace/DATABASE_ID?v=...
   ```
4. Share the database with your integration:
   - Click **Share** on the database
   - Click **Invite**
   - Select your Payment Tracker integration
   - Click **Invite**

## Environment Variables

Set these variables:

```bash
export NOTION_TOKEN="secret_your_integration_token"
export NOTION_DATABASE_ID="your_database_id"
```

## Database Schema

The following properties will be auto-created:

| Property | Type | Description |
|----------|------|-------------|
| Sender | Title | Payment sender name |
| Service | Select | Payment service (Wise, PayPal, etc.) |
| Amount | Number | Payment amount |
| Currency | Select | Currency code (USD, PHP, EUR, etc.) |
| Date | Date | Payment date |
| Subject | Rich Text | Email subject |
| Days Ago | Rich Text | Human-readable time |
| Message ID | Rich Text | Unique email identifier |
| From Email | Rich Text | Sender email address |
| To Email | Rich Text | Recipient email address |
| Extraction Timestamp | Rich Text | When record was created |
| Created | Created Time | Notion creation timestamp |
