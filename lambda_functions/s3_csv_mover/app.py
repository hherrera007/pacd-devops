import os
from urllib.parse import unquote_plus

import boto3


s3_client = boto3.client("s3")


def handler(event, _context):
    bucket_name = os.environ["BUCKET_NAME"]
    inbound_prefix = os.environ["INBOUND_PREFIX"]
    outbound_prefix = os.environ["OUTBOUND_PREFIX"]

    # S3 can send multiple object records in one event.
    for record in event["Records"]:
        source_bucket = record["s3"]["bucket"]["name"]
        source_key = unquote_plus(record["s3"]["object"]["key"])

        if source_bucket != bucket_name:
            continue

        if not source_key.startswith(inbound_prefix) or not source_key.endswith(".csv"):
            continue

        target_key = source_key.replace(inbound_prefix, outbound_prefix, 1)

        # Copy the CSV to outbound/ and remove the inbound copy.
        s3_client.copy_object(
            Bucket=bucket_name,
            CopySource={"Bucket": bucket_name, "Key": source_key},
            Key=target_key,
        )
        s3_client.delete_object(Bucket=bucket_name, Key=source_key)

    return {"status": "ok"}
