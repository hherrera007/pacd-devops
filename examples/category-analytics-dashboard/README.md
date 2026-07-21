# Category Analytics Dashboard

This folder contains a static dashboard for category click analytics.

## How to Use

1. Deploy the stack when you are ready.
2. Copy the CloudFormation output named `CategoryAnalyticsFunctionUrl`.
3. Replace this placeholder in `index.html`:

```javascript
const analyticsUrl = "https://REPLACE_WITH_CATEGORY_ANALYTICS_FUNCTION_URL/";
```

4. Open `index.html` in a browser.
5. Click `Refresh` to reload the charts.

## Charts

- `Clicks per Category`: bar chart with the total clicks per category.
- `Click Trend`: line chart grouped by category and minute.
- `Clicks per IP`: horizontal bar chart grouped by client IP.

Click an IP bar or IP button in `Clicks per IP` to filter the category and trend charts for that client IP. Use `Clear IP filter` to return to the global dashboard.

Hover over the larger points in the `Click Trend` line chart to see the bucket time, category, and click count.

The dashboard uses Chart.js from a public CDN.

## Downloads

Use the download buttons to export the raw `category_events` rows as:

- JSON
- CSV
- Parquet

If an IP filter is active, the downloaded file only includes rows for that IP.

Parquet export uses `pyarrow` in the analytics Lambda package, so Docker bundling downloads a larger dependency during deployment.

## Table

The dashboard reads from the PostgreSQL `category_events` table.

Table definition: [../../docs/example-category-events-table.md](../../docs/example-category-events-table.md)

## CORS

The dashboard must read JSON from the analytics Lambda, so it cannot use `no-cors`.

The analytics Lambda returns CORS headers directly and supports `GET` and `OPTIONS`.
