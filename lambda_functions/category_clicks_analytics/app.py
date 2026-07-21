import base64
import csv
import io
import json
import os

import pg8000.dbapi


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS category_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    category VARCHAR(100) NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    source_ip INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
"""


TOTALS_SQL = """
SELECT category, COUNT(*) AS clicks
FROM category_events
GROUP BY category
ORDER BY category;
"""


TOTALS_BY_IP_SQL = """
SELECT category, COUNT(*) AS clicks
FROM category_events
WHERE source_ip = %s::inet
GROUP BY category
ORDER BY category;
"""


TOTALS_UNKNOWN_IP_SQL = """
SELECT category, COUNT(*) AS clicks
FROM category_events
WHERE source_ip IS NULL
GROUP BY category
ORDER BY category;
"""


EVOLUTION_SQL = """
SELECT
    date_trunc('minute', event_time) AS bucket_start,
    category,
    COUNT(*) AS clicks
FROM category_events
GROUP BY bucket_start, category
ORDER BY bucket_start, category;
"""


EVOLUTION_BY_IP_SQL = """
SELECT
    date_trunc('minute', event_time) AS bucket_start,
    category,
    COUNT(*) AS clicks
FROM category_events
WHERE source_ip = %s::inet
GROUP BY bucket_start, category
ORDER BY bucket_start, category;
"""


EVOLUTION_UNKNOWN_IP_SQL = """
SELECT
    date_trunc('minute', event_time) AS bucket_start,
    category,
    COUNT(*) AS clicks
FROM category_events
WHERE source_ip IS NULL
GROUP BY bucket_start, category
ORDER BY bucket_start, category;
"""


CLICKS_BY_IP_SQL = """
SELECT COALESCE(source_ip::text, 'unknown') AS source_ip, COUNT(*) AS clicks
FROM category_events
GROUP BY source_ip
ORDER BY clicks DESC, source_ip;
"""


EVENTS_SQL = """
SELECT
    id,
    event_type,
    category,
    event_time,
    source_ip::text,
    user_agent,
    created_at
FROM category_events
ORDER BY event_time, id;
"""


EVENTS_BY_IP_SQL = """
SELECT
    id,
    event_type,
    category,
    event_time,
    source_ip::text,
    user_agent,
    created_at
FROM category_events
WHERE source_ip = %s::inet
ORDER BY event_time, id;
"""


EVENTS_UNKNOWN_IP_SQL = """
SELECT
    id,
    event_type,
    category,
    event_time,
    source_ip::text,
    user_agent,
    created_at
FROM category_events
WHERE source_ip IS NULL
ORDER BY event_time, id;
"""


def handler(event, _context):
    try:
        method = event.get("requestContext", {}).get("http", {}).get("method")

        if method == "OPTIONS":
            return response(204, {})
        if method != "GET":
            return response(405, {"message": "Use GET to read category click analytics."})

        connection = open_database_connection()
        try:
            # Ensures the dashboard returns empty data before the first event.
            ensure_table_exists(connection)
            selected_ip = get_selected_ip(event)

            download_format = get_download_format(event)
            if download_format:
                events = fetch_events(connection, selected_ip)
                return download_response(download_format, events, selected_ip)

            totals = fetch_totals(connection, selected_ip)
            evolution = fetch_evolution(connection, selected_ip)
            clicks_by_ip = fetch_clicks_by_ip(connection)
        finally:
            connection.close()

        return response(
            200,
            {
                "totals": totals,
                "evolution": evolution,
                "clicks_by_ip": clicks_by_ip,
                "selected_ip": selected_ip,
            },
        )
    except Exception as error:
        # Keeps browser errors readable instead of becoming opaque CORS failures.
        return response(500, {"message": str(error)})


def fetch_totals(connection, selected_ip=None):
    # Returns one total click count per category.
    cursor = connection.cursor()
    try:
        if selected_ip == "unknown":
            cursor.execute(TOTALS_UNKNOWN_IP_SQL)
        elif selected_ip:
            cursor.execute(TOTALS_BY_IP_SQL, (selected_ip,))
        else:
            cursor.execute(TOTALS_SQL)
        return [
            {
                "category": row[0],
                "clicks": int(row[1]),
            }
            for row in cursor.fetchall()
        ]
    finally:
        cursor.close()


def fetch_evolution(connection, selected_ip=None):
    # Groups clicks into 60-second buckets by category.
    cursor = connection.cursor()
    try:
        if selected_ip == "unknown":
            cursor.execute(EVOLUTION_UNKNOWN_IP_SQL)
        elif selected_ip:
            cursor.execute(EVOLUTION_BY_IP_SQL, (selected_ip,))
        else:
            cursor.execute(EVOLUTION_SQL)
        return [
            {
                "bucket_start": row[0].isoformat(),
                "category": row[1],
                "clicks": int(row[2]),
            }
            for row in cursor.fetchall()
        ]
    finally:
        cursor.close()


def fetch_clicks_by_ip(connection):
    # Returns total clicks grouped by client IP.
    cursor = connection.cursor()
    try:
        cursor.execute(CLICKS_BY_IP_SQL)
        return [
            {
                "source_ip": row[0],
                "clicks": int(row[1]),
            }
            for row in cursor.fetchall()
        ]
    finally:
        cursor.close()


def fetch_events(connection, selected_ip=None):
    # Returns raw rows used for JSON, CSV, and Parquet downloads.
    cursor = connection.cursor()
    try:
        if selected_ip == "unknown":
            cursor.execute(EVENTS_UNKNOWN_IP_SQL)
        elif selected_ip:
            cursor.execute(EVENTS_BY_IP_SQL, (selected_ip,))
        else:
            cursor.execute(EVENTS_SQL)

        return [
            {
                "id": row[0],
                "event_type": row[1],
                "category": row[2],
                "event_time": row[3].isoformat(),
                "source_ip": row[4],
                "user_agent": row[5],
                "created_at": row[6].isoformat(),
            }
            for row in cursor.fetchall()
        ]
    finally:
        cursor.close()


def get_selected_ip(event):
    # Optional dashboard filter: ?source_ip=<ip>.
    query_params = event.get("queryStringParameters") or {}
    selected_ip = (query_params.get("source_ip") or "").strip()
    return selected_ip or None


def get_download_format(event):
    # Optional download format: ?format=json|csv|parquet.
    query_params = event.get("queryStringParameters") or {}
    value = (query_params.get("format") or "").strip().lower()
    return value if value in {"json", "csv", "parquet"} else None


def download_response(download_format, events, selected_ip=None):
    if download_format == "json":
        return file_response(
            "application/json",
            build_file_name("category-events", selected_ip, "json"),
            json.dumps(events),
        )

    if download_format == "csv":
        return file_response(
            "text/csv",
            build_file_name("category-events", selected_ip, "csv"),
            events_to_csv(events),
        )

    return file_response(
        "application/vnd.apache.parquet",
        build_file_name("category-events", selected_ip, "parquet"),
        events_to_parquet(events),
        is_base64_encoded=True,
    )


def events_to_csv(events):
    output = io.StringIO()
    fieldnames = ["id", "event_type", "category", "event_time", "source_ip", "user_agent", "created_at"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(events)
    return output.getvalue()


def events_to_parquet(events):
    # Imported only for Parquet downloads to keep normal dashboard calls lighter.
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.Table.from_pylist(events)
    output = io.BytesIO()
    pq.write_table(table, output)
    return base64.b64encode(output.getvalue()).decode("ascii")


def build_file_name(base_name, selected_ip, extension):
    suffix = f"-{selected_ip}" if selected_ip else ""
    return f"{base_name}{suffix}.{extension}"


def ensure_table_exists(connection):
    # Keeps the endpoint safe before Firehose inserts the first row.
    cursor = connection.cursor()
    try:
        cursor.execute(CREATE_TABLE_SQL)
        connection.commit()
    finally:
        cursor.close()


def open_database_connection():
    # Uses the same demo database variables as the event loader Lambda.
    return pg8000.dbapi.connect(
        host=os.environ["DATABASE_HOST"],
        port=int(os.environ["DATABASE_PORT"]),
        database=os.environ["DATABASE_NAME"],
        user=os.environ["DATABASE_USERNAME"],
        password=os.environ["DATABASE_PASSWORD"],
    )


def response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
            "Access-Control-Allow-Headers": "content-type",
            "Content-Type": "application/json",
        },
        "body": json.dumps(body),
    }


def file_response(content_type, file_name, body, is_base64_encoded=False):
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET,OPTIONS",
            "Access-Control-Allow-Headers": "content-type",
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Content-Type": content_type,
        },
        "isBase64Encoded": is_base64_encoded,
        "body": body,
    }
