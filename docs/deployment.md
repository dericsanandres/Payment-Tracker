# Google Cloud Deployment

## Prerequisites

- Google Cloud account with billing enabled
- `gcloud` CLI installed and authenticated
- Project with Cloud Functions API enabled

## Enable Required APIs

```bash
gcloud services enable cloudfunctions.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

## Store Secrets

Create secrets for sensitive data:

```bash
# Create Gmail app password secret
echo -n "your-gmail-app-password" | gcloud secrets create gmail-app-password --data-file=-

# Create Notion token secret  
echo -n "secret_your-notion-token" | gcloud secrets create notion-token --data-file=-

# Create Notion database ID secret
echo -n "your-database-id" | gcloud secrets create notion-database-id --data-file=-
```

## Deploy Function

### Option 1: Manual Deployment

```bash
gcloud functions deploy payment-tracker \
  --runtime python39 \
  --trigger-http \
  --entry-point payment_extractor \
  --allow-unauthenticated \
  --set-env-vars GMAIL_USERNAME=dercsanandres@gmail.com \
  --set-secrets GMAIL_APP_PASSWORD=gmail-app-password:latest,NOTION_TOKEN=notion-token:latest,NOTION_DATABASE_ID=notion-database-id:latest \
  --memory 256MB \
  --timeout 540s
```

### Option 2: GitHub Actions (Recommended)

The repository includes a GitHub Actions workflow that automatically deploys on push to main.

1. Set up GitHub secrets:
   - `GCP_PROJECT_ID`: Your Google Cloud project ID
   - `GCP_SA_KEY`: Base64-encoded service account key JSON

2. Push to main branch to trigger deployment

## Schedule Function

Create a Cloud Scheduler job to run periodically:

```bash
gcloud scheduler jobs create http payment-tracker-schedule \
  --schedule="0 */6 * * *" \
  --uri="https://your-region-your-project.cloudfunctions.net/payment-tracker" \
  --http-method=POST \
  --headers="Content-Type=application/json" \
  --message-body='{}' \
  --time-zone="UTC"
```

## Monitor Function

View logs:
```bash
gcloud functions logs read payment-tracker --limit 50
```

Check function status:
```bash
gcloud functions describe payment-tracker
```

## Testing

Test the deployed function:
```bash
curl -X POST "https://your-region-your-project.cloudfunctions.net/payment-tracker" \
  -H "Content-Type: application/json" \
  -d '{"test": true}'
```
