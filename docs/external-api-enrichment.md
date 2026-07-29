# External API Product Cache

This demo creates a public Lambda Function URL that calls one external product API with `requests`, filters products by category, and caches the category result in S3.

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

Paste the deployed `ExternalApiEnrichmentFunctionUrl`, select a category, and load products. The first request for a category writes one JSON cache file to S3; repeated requests for the same category read that S3 file instead of calling the API again.

## Storage

The Lambda writes JSON files under:

```text
s3://<EXTERNAL_API_BUCKET_NAME>/external-api-enrichment/category-cache/
```

Each file includes:

- selected category
- source API URL
- source error, if the API failed
- product count
- filtered products

The cache key is based on the requested category, so a repeated category request returns the existing S3 object.

The demo categories must match the category names returned by `PRODUCTS_API_URL`. The current dashboard uses real categories from `https://api.escuelajs.co/api/v1/products`, such as `Electronics`, `Shoes`, `Miscellaneous`, and `pet supplies`.

## Configuration

Set these values in `.env`:

```text
EXTERNAL_API_BUCKET_NAME=<GLOBALLY_UNIQUE_EXTERNAL_API_BUCKET_NAME>
PRODUCTS_API_URL=https://api.escuelajs.co/api/v1/products
```

S3 bucket names must be globally unique across all AWS accounts.

## CORS

The Lambda Function URL handles CORS for the browser dashboard. The Lambda response only returns `Content-Type` to avoid duplicate `Access-Control-Allow-Origin` headers.
