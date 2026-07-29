# Crypto Prices Dashboard

This folder contains a static dashboard for live crypto prices.

## How to Use

1. Deploy the stack when you are ready.
2. Copy the CloudFormation output named `CryptoPricesFunctionUrl`.
3. Open `index.html`.
4. Replace the placeholder URL in the page input with the deployed Function URL.
5. The line plots refresh automatically every 10 seconds.

The page updates only the chart data and price labels on refresh; it does not rebuild the full page.

The Lambda uses S3 as a shared 10-second cache, so multiple computers can reuse the same recent price payload.

## Coins

- Bitcoin: `BTCUSDT`
- Ethereum: `ETHUSDT`
- Dogecoin: `DOGEUSDT`

The Lambda reads prices from Binance:

```text
https://data-api.binance.vision/api/v3/ticker/price
```

Coin logos are loaded from CryptoLogos.

The crypto prices Lambda uses `requests`, so Docker must be running when CDK bundles the Lambda asset.
