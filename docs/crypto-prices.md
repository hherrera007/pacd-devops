# Crypto Prices

This demo creates a public Lambda Function URL that reads Binance ticker prices for:

- `BTCUSDT`
- `ETHUSDT`
- `DOGEUSDT`

## Resources

- Lambda Function URL: `CryptoPricesFunctionUrl`
- Lambda: `crypto-prices`

The Lambda is intentionally outside the VPC so it can call Binance without a NAT Gateway.

The Lambda uses `requests`, so Docker must be running when CDK bundles the Lambda asset.

## Configuration

Set this value in `.env`:

```text
BINANCE_PRICE_URL=https://data-api.binance.vision/api/v3/ticker/price
```

## Request

```bash
curl "<CryptoPricesFunctionUrl>"
```

## Dashboard

Open the static dashboard at:

```text
examples/crypto-prices-dashboard/index.html
```

Paste the deployed `CryptoPricesFunctionUrl`. The dashboard refreshes every 10 seconds and updates only the line plots and price labels.

## Shared Cache

The Lambda uses S3 as a shared 10-second cache:

```text
s3://<EXTERNAL_API_BUCKET_NAME>/crypto-prices/latest.json
```

If another computer calls the same Lambda within 10 seconds, the Lambda returns the cached S3 payload instead of calling Binance again.

## Cost

Creating the Lambda has no fixed hourly cost. You pay for requests, execution duration, CloudWatch Logs, and the small S3 GET/PUT requests used by the shared cache.
