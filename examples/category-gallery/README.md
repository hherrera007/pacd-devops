# Category Gallery Demo

This folder contains a static HTML page that shows product categories and sends the selected category to a public Lambda Function URL.

## How to Use

1. Deploy the stack when you are ready.
2. Copy the CloudFormation output named `CategoryEventFunctionUrl`.
3. Replace this placeholder in `index.html`:

```javascript
const categoryEventUrl = "https://REPLACE_WITH_CATEGORY_EVENT_FUNCTION_URL/";
```

4. Open `index.html` in a browser.
5. Click a category image.

The page displays:

```text
nice choice, you choose <category>
```

It also sends this JSON payload to the Lambda URL:

```json
{
  "category": "Electronics"
}
```

The page does not wait for the Lambda response. It updates the selected category message immediately and lets the request continue in the background.

## What AWS Stores

The Lambda adds the UTC date-time, source IP, and user agent, then sends the event to Amazon Data Firehose. Firehose stores the records in S3 as JSON Lines files.

The expected stored record shape is:

```json
{
  "event_type": "category_selected",
  "category": "Electronics",
  "event_time": "2026-07-07T18:30:00.000+00:00",
  "source_ip": "203.0.113.10",
  "user_agent": "Mozilla/5.0 ..."
}
```

## Security Note

This is a public demo endpoint. Anyone with the URL can send category events.
