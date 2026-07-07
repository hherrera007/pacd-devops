import json
import os
from datetime import datetime, timezone

import boto3


firehose_client = boto3.client("firehose")


def handler(event, _context):
    # Accepts only browser POST events from the category page.
    if event.get("requestContext", {}).get("http", {}).get("method") != "POST":
        return response(405, "Use POST to send a category event.")

    payload = parse_body(event)
    # Trims the selected category before storing it.
    category = str(payload.get("category", "")).strip()

    if not category:
        return response(400, "category is required.")

    http_context = event.get("requestContext", {}).get("http", {})
    # Adds request metadata useful for the demo analysis.
    record = {
        "event_type": "category_selected",
        "category": category,
        "event_time": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
        "source_ip": http_context.get("sourceIp", ""),
        "user_agent": http_context.get("userAgent", ""),
    }

    # Firehose expects bytes; newline makes S3 output JSON Lines friendly.
    firehose_client.put_record(
        DeliveryStreamName=os.environ["DELIVERY_STREAM_NAME"],
        Record={"Data": (json.dumps(record) + "\n").encode("utf-8")},
    )

    return response(202, record)


def parse_body(event):
    # Returns an empty payload when JSON is missing or invalid.
    body = event.get("body") or "{}"
    try:
        return json.loads(body)
    except json.JSONDecodeError:
        return {}


def response(status_code, body):
    # Keeps Function URL responses simple for the browser demo.
    return {
        "statusCode": status_code,
        "headers": {"content-type": "application/json"},
        "body": json.dumps(body),
    }
