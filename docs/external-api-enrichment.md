# External API Comparison

This demo creates a public Lambda Function URL that calls two external product APIs with `requests`, compares the category-filtered responses, and stores the raw and comparison payload in S3.

## Resources

- Lambda Function URL: `ExternalApiEnrichmentFunctionUrl`
- Lambda: `external-api-enrichment`
- S3 bucket: configured by `EXTERNAL_API_BUCKET_NAME`

The Lambda is intentionally outside the VPC so it can call public internet APIs without a NAT Gateway.

## Request

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d "{\"category\":\"Electronics\"}" \
  "<ExternalApiEnrichmentFunctionUrl>"
```

## Dashboard

Open the static dashboard at:

```text
examples/external-api-enrichment-dashboard/index.html
```

Paste the deployed `ExternalApiEnrichmentFunctionUrl`, select a category, and run the comparison. Each successful dashboard run writes one JSON file to S3.

## Storage

The Lambda writes JSON files under:

```text
s3://<EXTERNAL_API_BUCKET_NAME>/external-api-enrichment/
```

Each file includes:

- selected category
- source API URLs
- source errors, warnings, and matching product counts
- filtered raw API responses
- product comparisons

The comparison pairs products by list position after filtering each API by category. The two APIs do not share product IDs, so this is not a true product merge. If one API has no matching products, it is left empty instead of filling the response with unrelated fallback products.

## Configuration

Set these values in `.env`:

```text
EXTERNAL_API_BUCKET_NAME=<GLOBALLY_UNIQUE_EXTERNAL_API_BUCKET_NAME>
PRODUCTS_API_ONE_URL=https://fakestoreapi.com/products
PRODUCTS_API_TWO_URL=https://api.escuelajs.co/api/v1/products
```

S3 bucket names must be globally unique across all AWS accounts.

## CORS

The Lambda Function URL handles CORS for the browser dashboard. The Lambda response only returns `Content-Type` to avoid duplicate `Access-Control-Allow-Origin` headers.
