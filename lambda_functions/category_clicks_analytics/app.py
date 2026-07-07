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


EVOLUTION_SQL = """
SELECT
    date_trunc('minute', event_time) AS bucket_start,
    category,
    COUNT(*) AS clicks
FROM category_events
GROUP BY bucket_start, category
ORDER BY bucket_start, category;
"""


CLICKS_BY_IP_SQL = """
SELECT COALESCE(source_ip::text, 'unknown') AS source_ip, COUNT(*) AS clicks
FROM category_events
GROUP BY source_ip
ORDER BY clicks DESC, source_ip;
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
            totals = fetch_totals(connection)
            evolution = fetch_evolution(connection)
            clicks_by_ip = fetch_clicks_by_ip(connection)
        finally:
            connection.close()

        return response(
            200,
            {
                "totals": totals,
                "evolution": evolution,
                "clicks_by_ip": clicks_by_ip,
            },
        )
    except Exception as error:
        # Keeps browser errors readable instead of becoming opaque CORS failures.
        return response(500, {"message": str(error)})


def fetch_totals(connection):
    # Returns one total click count per category.
    cursor = connection.cursor()
    try:
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


def fetch_evolution(connection):
    # Groups clicks into 60-second buckets by category.
    cursor = connection.cursor()
    try:
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
