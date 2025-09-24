# API Reference

## Endpoints

### POST /

Main payment extraction endpoint.

#### Request Body

```json
{
  "test": false  // Optional: set to true for configuration test
}
```

#### Response - Success

```json
{
  "status": "success",
  "payments_processed": 5,
  "database_result": {
    "created": 3,
    "skipped_duplicates": 2,
    "failed": 0,
    "errors": []
  },
  "summary": {
    "services": ["Wise", "Paypal"],
    "total_amount": 1250.50,
    "currencies": ["USD", "PHP"]
  }
}
```

#### Response - Test Mode

```json
{
  "status": "healthy",
  "message": "Payment extractor is running",
  "config_loaded": true
}
```

#### Response - Error

```json
{
  "status": "error",
  "message": "Missing configuration: ['DATABASE_TOKEN']"
}
```

### GET /health

Health check endpoint.

#### Response

```json
{
  "status": "healthy",
  "service": "payment-extractor"
}
```

## Data Structures

### Payment Object

```json
{
  "service": "Wise",
  "sender": "John Doe",
  "amount": "100.50",
  "currency": "USD",
  "date": "Thu, 01 Jun 2025 10:30:00 +0000",
  "days_ago": "3 days ago",
  "subject": "You've got paid",
  "message_id": "unique-message-id",
  "from_email": "noreply@wise.com",
  "to_email": "dercsanandres@gmail.com",
  "extraction_timestamp": "2025-06-04T15:30:00.123456"
}
```

### Database Result Object

```json
{
  "created": 3,           // Successfully created records
  "skipped_duplicates": 2, // Duplicate records skipped
  "failed": 0,            // Failed to create
  "errors": []            // List of error messages
}
```

## Error Codes

| Status Code | Description |
|-------------|-------------|
| 200 | Success |
| 500 | Internal server error |

## Rate Limits

- Gmail IMAP: 250 quota units per user per second
- Database API: 3 requests per second
- Function timeout: 540 seconds (9 minutes)

## Supported Payment Services

| Service | Email Pattern | Currency Support |
|---------|---------------|------------------|
| Wise | `noreply@wise.com` | USD, EUR, GBP, PHP, CAD |
| PayPal | `service@paypal.com` | USD, EUR, GBP, PHP, CAD |
| Remitly | `no-reply@remitly.com` | USD, PHP |
| Bill.com | `account-services@hq.bill.com` | USD |
