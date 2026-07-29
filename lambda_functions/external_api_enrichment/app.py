import json
import os
from datetime import datetime, timezone
from urllib.parse import quote

import boto3
import requests
from requests import RequestException
from botocore.exceptions import ClientError


s3_client = boto3.client("s3")


def handler(event, _context):
    # Handles public Function URL requests.
    method = event.get("requestContext", {}).get("http", {}).get("method")

    if method == "OPTIONS":
        return response(204, {})
    if method != "POST":
        return response(405, {"message": "Use POST to enrich external product data."})

    payload = parse_body(event)
    category = str(payload.get("category", "")).strip() or "Electronics"
    cache_key = category_cache_key(category)

    # Reuses the S3 category cache before calling the external API.
    cached_payload = read_cached_payload(cache_key)
    if cached_payload:
        cached_payload["cache_hit"] = True
        return response(200, cached_payload)

    # Calls the source API only when the category is not cached.
    api_result = fetch_products(os.environ["PRODUCTS_API_URL"])
    filtered_products = [normalize_product(product) for product in filter_products(api_result["products"], category)]
    stored_payload = {
        "category": category,
        "cached_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "cache_hit": False,
        "s3_key": None if api_result["error"] else cache_key,
        "source_url": os.environ["PRODUCTS_API_URL"],
        "source_error": api_result["error"],
        "product_count": len(filtered_products),
        "products": filtered_products,
    }

    # Avoids caching temporary external API failures.
    if not api_result["error"]:
        store_payload(cache_key, stored_payload)
    return response(200, stored_payload)


def fetch_products(url):
    # Calls one external API using requests.
    try:
        print(f"Calling external products API: {url}")
        api_response = requests.get(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 "
                    "Chrome/150.0.0.0 Safari/537.36"
                ),
                "Accept": "application/json",
            },
            timeout=15,
        )
        api_response.raise_for_status()
        payload = api_response.json()
    except RequestException as error:
        print(f"External products API failed: url={url}, error={error}")
        return {"products": [], "error": str(error)}

    if isinstance(payload, list):
        print(f"External products API succeeded: url={url}, products={len(payload)}")
        return {"products": payload, "error": None}
    if isinstance(payload, dict):
        products = payload.get("products") or payload.get("data") or []
        print(f"External products API succeeded: url={url}, products={len(products)}")
        return {"products": products, "error": None}

    print(f"External products API returned unsupported JSON: url={url}")
    return {"products": [], "error": "The API returned an unsupported JSON shape."}


def filter_products(products, category):
    # Keeps only products that match the requested category.
    expected_category = category.strip().lower()
    matches = [
        product
        for product in products
        if product_category_name(product).lower() == expected_category
    ]
    return matches[:10]


def product_category_name(product):
    # Supports APIs that return category as a string or object.
    category = product.get("category")
    if isinstance(category, dict):
        return str(category.get("name") or "")
    return str(category or product.get("categoryName") or "")


def normalize_product(product):
    # Returns only the fields used by the dashboard.
    return {
        "id": product.get("id"),
        "title": product.get("title") or product.get("name"),
        "category": normalize_category(product.get("category")),
        "price": product.get("price"),
        "image": product.get("image") or product.get("images"),
    }


def normalize_category(value):
    if isinstance(value, dict):
        return value.get("name")
    return value


def category_cache_key(category):
    # Creates one stable S3 cache file per requested category.
    safe_category = quote(category.strip().lower().replace(" ", "-"), safe="-")
    return f"{os.environ['OUTPUT_PREFIX']}category-cache/{safe_category}.json"


def read_cached_payload(object_key):
    # Missing cache files are expected on first category request.
    try:
        cached_object = s3_client.get_object(
            Bucket=os.environ["BUCKET_NAME"],
            Key=object_key,
        )
    except ClientError as error:
        if error.response.get("Error", {}).get("Code") in ["NoSuchKey", "404"]:
            return None
        raise

    print(f"Using cached category payload from S3: {object_key}")
    return json.loads(cached_object["Body"].read().decode("utf-8"))


def store_payload(object_key, payload):
    # Stores the normalized category result for future requests.
    s3_client.put_object(
        Bucket=os.environ["BUCKET_NAME"],
        Key=object_key,
        Body=json.dumps(payload).encode("utf-8"),
        ContentType="application/json",
    )


def parse_body(event):
    # Keeps invalid JSON from crashing the demo endpoint.
    body = event.get("body") or "{}"
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}


def response(status_code, body):
    # Function URL CORS is configured in CDK.
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body),
    }
