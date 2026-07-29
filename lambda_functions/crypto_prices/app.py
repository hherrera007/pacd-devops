import json
import os
from datetime import datetime, timezone
from urllib.parse import urlencode

import boto3
import requests
from requests import RequestException
from botocore.exceptions import ClientError


s3_client = boto3.client("s3")


COINS = [
    {"name": "Bitcoin", "symbol": "BTC", "pair": "BTCUSDT"},
    {"name": "Ethereum", "symbol": "ETH", "pair": "ETHUSDT"},
    {"name": "Dogecoin", "symbol": "DOGE", "pair": "DOGEUSDT"},
]


def handler(event, _context):
    # Handles public Function URL requests.
    method = event.get("requestContext", {}).get("http", {}).get("method")

    if method == "OPTIONS":
        return response(204, {})
    if method != "GET":
        return response(405, {"message": "Use GET to read crypto prices."})

    # Returns shared S3 cache when it is still inside the TTL.
    cached_payload = read_cached_prices()
    if cached_payload:
        cached_payload["cache_hit"] = True
        return response(200, cached_payload)

    # Refreshes all coin prices after a cache miss.
    prices = [read_coin_price(coin) for coin in COINS]
    payload = {
        "source": "binance",
        "cache_hit": False,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "cache_ttl_seconds": cache_ttl_seconds(),
        "prices": prices,
    }
    store_cached_prices(payload)
    return response(200, payload)


def read_coin_price(coin):
    # Calls Binance ticker price for one USDT pair.
    query = urlencode({"symbol": coin["pair"]})
    url = f"{os.environ['BINANCE_PRICE_URL']}?{query}"

    try:
        api_response = requests.get(
            url,
            headers={"Accept": "application/json"},
            timeout=8,
        )
        api_response.raise_for_status()
        payload = api_response.json()
    except RequestException as error:
        print(f"Binance price request failed: pair={coin['pair']}, error={error}")
        return {
            **coin,
            "price": None,
            "error": str(error),
        }

    return {
        **coin,
        "price": float(payload["price"]),
        "error": None,
    }


def read_cached_prices():
    # Shares one short-lived S3 cache across all dashboard clients.
    try:
        cached_object = s3_client.get_object(
            Bucket=os.environ["BUCKET_NAME"],
            Key=os.environ["CACHE_KEY"],
        )
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") in ["NoSuchKey", "404"]:
            return None
        raise

    payload = json.loads(cached_object["Body"].read().decode("utf-8"))
    fetched_at = datetime.fromisoformat(payload["fetched_at"])
    age_seconds = (datetime.now(timezone.utc) - fetched_at).total_seconds()

    if age_seconds > cache_ttl_seconds():
        return None

    print(f"Using cached crypto prices from S3: age_seconds={age_seconds:.2f}")
    return payload


def store_cached_prices(payload):
    # Updates the shared cache after a fresh Binance read.
    s3_client.put_object(
        Bucket=os.environ["BUCKET_NAME"],
        Key=os.environ["CACHE_KEY"],
        Body=json.dumps(payload).encode("utf-8"),
        ContentType="application/json",
    )


def cache_ttl_seconds():
    # CDK maps CRYPTO_PRICE_CACHE_TTL_SECONDS into this Lambda variable.
    return int(os.environ["CACHE_TTL_SECONDS"])


def response(status_code, body):
    # Function URL CORS is configured in CDK.
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body),
    }
