# External API Product Dashboard

This folder contains a static dashboard for the external API product cache Lambda.

## How to Use

1. Deploy the stack when you are ready.
2. Copy the CloudFormation output named `ExternalApiEnrichmentFunctionUrl`.
3. Open `index.html`.
4. Replace the placeholder URL in the page input with the deployed Function URL.
5. Choose a category and click `Load Products`.

The first successful request for a category calls the external products API and writes one JSON cache file to:

```text
s3://<EXTERNAL_API_BUCKET_NAME>/external-api-enrichment/category-cache/
```

Repeated requests for the same category read the existing S3 cache file instead of calling the external API again.

## What the Dashboard Shows

- Selected category.
- Number of products.
- S3 object key where the category cache payload was stored.
- Product cards from the external API.
- Cache hit or cache miss status.
- Image carousel when a product returns more than one image URL.
- Default placeholder image when a product image URL fails.
- Raw Lambda response for debugging.

## Configuration

The dashboard calls this Lambda URL:

```text
ExternalApiEnrichmentFunctionUrl
```

The Lambda uses these `.env` variables from the stack:

```text
EXTERNAL_API_BUCKET_NAME=<GLOBALLY_UNIQUE_EXTERNAL_API_BUCKET_NAME>
PRODUCTS_API_URL=https://api.escuelajs.co/api/v1/products
```

S3 bucket names must be globally unique across all AWS accounts.

## CORS

The dashboard sends a browser `POST` request to the Lambda Function URL.

The Lambda Function URL allows `POST` and `OPTIONS` requests from any origin for this demo.
