import base64
import os
from datetime import datetime, timezone
from uuid import uuid4

import boto3


s3_client = boto3.client("s3")


def handler(event, _context):
    # Accept only CSV uploads sent through POST.
    if event.get("requestContext", {}).get("http", {}).get("method") != "POST":
        return response(405, "Use POST to upload a CSV file.")

    # Reject non-CSV requests early.
    content_type = get_header(event, "content-type")
    if "text/csv" not in content_type.lower():
        return response(400, "Content-Type must be text/csv.")

    body = event.get("body")
    if not body:
        return response(400, "CSV body is required.")

    # Decode the Function URL body and store it under inbound/.
    file_body = decode_body(body, event.get("isBase64Encoded", False))
    filename = build_filename()
    target_key = f"{os.environ['INBOUND_PREFIX']}{filename}"

    s3_client.put_object(
        Bucket=os.environ["BUCKET_NAME"],
        Key=target_key,
        Body=file_body,
        ContentType="text/csv",
    )

    return response(201, f"Uploaded to {target_key}")


def get_header(event, header_name):
    # Function URL headers can arrive with different casing.
    headers = event.get("headers") or {}
    for key, value in headers.items():
        if key.lower() == header_name:
            return value or ""
    return ""


def decode_body(body, is_base64_encoded):
    if is_base64_encoded:
        return base64.b64decode(body)
    return body.encode("utf-8")


def build_filename():
    # Rename every upload to avoid collisions and unsafe names.
    now = datetime.now(timezone.utc)
    timestamp = now.strftime("%Y%m%dT%H%M%S") + f"{now.microsecond // 1000:03d}Z"
    return f"upload-{timestamp}-{uuid4().hex}.csv"


def response(status_code, message):
    return {
        "statusCode": status_code,
        "headers": {"content-type": "text/plain"},
        "body": message,
    }
