import csv
import os
from datetime import date
from decimal import Decimal, InvalidOperation
from io import StringIO
from urllib.parse import unquote_plus

import boto3


s3_client = boto3.client("s3")

EXPECTED_HEADERS = [
    "fecha",
    "producto",
    "categoria",
    "cantidad",
    "precio_unitario",
    "cliente",
]


def handler(event, _context):
    bucket_name = os.environ["BUCKET_NAME"]
    incoming_prefix = os.environ["INBOUND_PREFIX"]

    # S3 can send multiple object records in one event.
    for record in event["Records"]:
        source_bucket = record["s3"]["bucket"]["name"]
        source_key = unquote_plus(record["s3"]["object"]["key"])

        if source_bucket != bucket_name:
            continue

        if not source_key.startswith(incoming_prefix) or not source_key.endswith(".csv"):
            continue

        process_csv_file(bucket_name, source_key)

    return {"status": "ok"}


def process_csv_file(bucket_name, source_key):
    csv_content = read_s3_text(bucket_name, source_key)
    reader = csv.DictReader(StringIO(csv_content))
    invalid_rows = []

    header_error = validate_header(reader.fieldnames)

    for row in reader:
        clean_row = clean_text_fields(row)

        if header_error:
            invalid_rows.append(add_error(clean_row, header_error))
            continue

        errors, _parsed_row = validate_row(clean_row)
        if errors:
            invalid_rows.append(add_error(clean_row, "; ".join(errors)))
            continue

        # Database insert disabled while troubleshooting Lambda errors.
        # insert_sale(connection, parsed_row, clean_row)

    if invalid_rows:
        write_invalid_rows(bucket_name, source_key, invalid_rows)


def read_s3_text(bucket_name, source_key):
    response = s3_client.get_object(Bucket=bucket_name, Key=source_key)
    return response["Body"].read().decode("utf-8-sig")


def validate_header(fieldnames):
    if not fieldnames:
        return f"Invalid header. Expected: {', '.join(EXPECTED_HEADERS)}"

    headers = [field.strip() for field in fieldnames]
    if headers != EXPECTED_HEADERS:
        return f"Invalid header. Expected: {', '.join(EXPECTED_HEADERS)}"

    return None


def clean_text_fields(row):
    # Trim spaces from every CSV value while preserving the original columns.
    clean_row = {}
    for key, value in row.items():
        clean_key = key.strip() if isinstance(key, str) else "extra_columns"
        clean_value = "|".join(value) if isinstance(value, list) else value
        clean_row[clean_key] = clean_value.strip() if isinstance(clean_value, str) else clean_value

    return clean_row


def validate_row(row):
    errors = []
    parsed_row = {}

    if row.get("extra_columns"):
        errors.append("row has extra columns")

    if not row.get("fecha"):
        errors.append("fecha must not be empty")
    else:
        try:
            date.fromisoformat(row["fecha"])
        except ValueError:
            errors.append("fecha must use YYYY-MM-DD format")

    if not row.get("producto"):
        errors.append("producto must not be empty")

    if not row.get("categoria"):
        errors.append("categoria must not be empty")

    if not row.get("cliente"):
        errors.append("cliente must not be empty")

    cantidad = parse_positive_integer(row.get("cantidad"))
    if cantidad is None:
        errors.append("cantidad must be greater than zero")
    else:
        parsed_row["cantidad"] = cantidad

    precio_unitario = parse_positive_decimal(row.get("precio_unitario"))
    if precio_unitario is None:
        errors.append("precio_unitario must be greater than zero")
    else:
        parsed_row["precio_unitario"] = precio_unitario

    if errors:
        return errors, parsed_row

    parsed_row["total"] = parsed_row["cantidad"] * parsed_row["precio_unitario"]
    return errors, parsed_row


def parse_positive_integer(value):
    try:
        parsed_value = int(value)
    except (TypeError, ValueError):
        return None

    return parsed_value if parsed_value > 0 else None


def parse_positive_decimal(value):
    try:
        parsed_value = Decimal(value)
    except (InvalidOperation, TypeError):
        return None

    return parsed_value if parsed_value > 0 else None


def add_error(row, error_message):
    return {**row, "error_message": error_message}


def write_invalid_rows(bucket_name, source_key, invalid_rows):
    output = StringIO()
    fieldnames = build_invalid_fieldnames(invalid_rows)
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(invalid_rows)

    target_key = source_key.replace(
        os.environ["INBOUND_PREFIX"],
        os.environ["OUTBOUND_PREFIX"],
        1,
    )

    s3_client.put_object(
        Bucket=bucket_name,
        Key=target_key,
        Body=output.getvalue().encode("utf-8"),
        ContentType="text/csv",
    )


def build_invalid_fieldnames(invalid_rows):
    fieldnames = []
    for row in invalid_rows:
        for fieldname in row.keys():
            if fieldname != "error_message" and fieldname not in fieldnames:
                fieldnames.append(fieldname)

    return fieldnames + ["error_message"]
