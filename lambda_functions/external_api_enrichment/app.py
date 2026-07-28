import json
import os
import uuid
from datetime import datetime, timezone

import boto3
import requests
from requests import RequestException


s3_client = boto3.client("s3")


def handler(event, _context):
    method = event.get("requestContext", {}).get("http", {}).get("method")

    if method == "OPTIONS":
        return response(204, {})
    if method != "POST":
        return response(405, {"message": "Use POST to enrich external product data."})

    payload = parse_body(event)
    category = str(payload.get("category", "")).strip() or "Electronics"

    api_one_result = fetch_products(os.environ["PRODUCTS_API_ONE_URL"])
    api_two_result = fetch_products(os.environ["PRODUCTS_API_TWO_URL"])
    api_one_products = api_one_result["products"]
    api_two_products = api_two_result["products"]

    filtered_one = filter_products(api_one_products, category)
    filtered_two = filter_products(api_two_products, category)
    product_comparisons = compare_products(filtered_one, filtered_two, category)
    source_warnings = build_source_warnings(filtered_one, filtered_two)

    stored_payload = {
        "category": category,
        "compared_at": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "source_urls": {
            "api_one": os.environ["PRODUCTS_API_ONE_URL"],
            "api_two": os.environ["PRODUCTS_API_TWO_URL"],
        },
        "source_errors": {
            "api_one": api_one_result["error"],
            "api_two": api_two_result["error"],
        },
        "source_warnings": source_warnings,
        "source_counts": {
            "api_one": len(filtered_one),
            "api_two": len(filtered_two),
        },
        "raw": {
            "api_one": filtered_one,
            "api_two": filtered_two,
        },
        "comparisons": product_comparisons,
    }

    object_key = store_payload(stored_payload)

    return response(
        200,
        {
            "category": category,
            "comparison_count": len(product_comparisons),
            "s3_key": object_key,
            "source_errors": stored_payload["source_errors"],
            "source_warnings": source_warnings,
            "source_counts": stored_payload["source_counts"],
            "comparisons": product_comparisons,
        },
    )


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
    category_terms = category.lower().replace("&", " ").split()
    matches = [
        product
        for product in products
        if product_matches_category(product, category_terms)
    ]
    return matches[:10]


def build_source_warnings(api_one_products, api_two_products):
    warnings = {}

    if not api_one_products:
        warnings["api_one"] = "No products matched the requested category."
    if not api_two_products:
        warnings["api_two"] = "No products matched the requested category."

    return warnings


def product_matches_category(product, category_terms):
    searchable = " ".join(
        str(product.get(key, ""))
        for key in ["category", "categoryName", "title", "name", "description"]
    ).lower()
    return any(term in searchable for term in category_terms)


def compare_products(api_one_products, api_two_products, category):
    # Compares products by list position; the APIs do not share product IDs.
    comparisons = []
    max_items = max(len(api_one_products), len(api_two_products))

    for index in range(max_items):
        api_one = api_one_products[index] if index < len(api_one_products) else {}
        api_two = api_two_products[index] if index < len(api_two_products) else {}
        comparisons.append(
            {
                "category": category,
                "api_one_product": normalize_product(api_one),
                "api_two_product": normalize_product(api_two),
            }
        )

    return comparisons


def normalize_product(product):
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


def store_payload(payload):
    now = datetime.now(timezone.utc)
    object_key = (
        f"{os.environ['OUTPUT_PREFIX']}"
        f"year={now:%Y}/month={now:%m}/day={now:%d}/"
        f"external-api-comparison-{now:%Y%m%dT%H%M%S%fZ}-{uuid.uuid4()}.json"
    )
    s3_client.put_object(
        Bucket=os.environ["BUCKET_NAME"],
        Key=object_key,
        Body=json.dumps(payload).encode("utf-8"),
        ContentType="application/json",
    )
    return object_key


def parse_body(event):
    body = event.get("body") or "{}"
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body),
    }
