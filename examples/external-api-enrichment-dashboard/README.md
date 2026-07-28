# External API Comparison Dashboard

This folder contains a static dashboard for the external API comparison Lambda.

## How to Use

1. Deploy the stack when you are ready.
2. Copy the CloudFormation output named `ExternalApiEnrichmentFunctionUrl`.
3. Open `index.html`.
4. Replace the placeholder URL in the page input with the deployed Function URL.
5. Choose a category and click `Run Comparison`.

Every successful run calls two external product APIs, compares the category-filtered products, and writes one JSON file to:

```text
s3://<EXTERNAL_API_BUCKET_NAME>/external-api-enrichment/
```

## What the Dashboard Shows

- Selected category.
- Number of compared products.
- S3 object key where the comparison payload was stored.
- Product comparison cards for API one and API two.
- Image carousel when a product returns more than one image URL.
- Raw Lambda response for debugging.

## Configuration

The dashboard calls this Lambda URL:

```text
ExternalApiEnrichmentFunctionUrl
```

The Lambda uses these `.env` variables from the stack:

```text
EXTERNAL_API_BUCKET_NAME=<GLOBALLY_UNIQUE_EXTERNAL_API_BUCKET_NAME>
PRODUCTS_API_ONE_URL=https://fakestoreapi.com/products
PRODUCTS_API_TWO_URL=https://api.escuelajs.co/api/v1/products
```

S3 bucket names must be globally unique across all AWS accounts.

## CORS

The dashboard sends a browser `POST` request to the Lambda Function URL.

The Lambda Function URL allows `POST` and `OPTIONS` requests from any origin for this demo.
