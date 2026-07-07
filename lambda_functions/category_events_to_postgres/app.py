import json
import os
from urllib.parse import unquote_plus

import boto3
import pg8000.dbapi


s3_client = boto3.client("s3")


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


INSERT_EVENT_SQL = """
INSERT INTO category_events (
    event_type,
    category,
    event_time,
    source_ip,
    user_agent
) VALUES (%s, %s, %s, %s, %s);
"""


def handler(event, _context):
    inserted = 0
    # Opens one DB connection for all S3 records in this invocation.
    connection = open_database_connection()

    try:
        # Creates the demo table if it does not exist yet.
        ensure_table_exists(connection)

        for record in event.get("Records", []):
            # S3 event gives the Firehose object that was just created.
            bucket_name = record["s3"]["bucket"]["name"]
            object_key = unquote_plus(record["s3"]["object"]["key"])
            inserted += insert_events_from_object(connection, bucket_name, object_key)

        # Commits all inserted rows together.
        connection.commit()
    finally:
        connection.close()

    return {
        "statusCode": 200,
        "body": json.dumps({"inserted": inserted}),
    }


def insert_events_from_object(connection, bucket_name, object_key):
    # Firehose stores records as newline-delimited JSON.
    response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
    body = response["Body"].read().decode("utf-8")
    inserted = 0

    for line in body.splitlines():
        if not line.strip():
            continue

        # Each line is one category event.
        event = json.loads(line)
        insert_event(connection, event)
        inserted += 1

    return inserted


def insert_event(connection, event):
    # Inserts one JSON Lines event created by Firehose.
    cursor = connection.cursor()
    try:
        cursor.execute(
            INSERT_EVENT_SQL,
            (
                event["event_type"],
                event["category"],
                event["event_time"],
                event.get("source_ip") or None,
                event.get("user_agent") or None,
            ),
        )
    finally:
        cursor.close()


def ensure_table_exists(connection):
    # Makes the demo idempotent across fresh databases.
    cursor = connection.cursor()
    try:
        cursor.execute(CREATE_TABLE_SQL)
    finally:
        cursor.close()


def open_database_connection():
    # Uses the same demo database variables as the CSV loader Lambda.
    return pg8000.dbapi.connect(
        host=os.environ["DATABASE_HOST"],
        port=int(os.environ["DATABASE_PORT"]),
        database=os.environ["DATABASE_NAME"],
        user=os.environ["DATABASE_USERNAME"],
        password=os.environ["DATABASE_PASSWORD"],
    )
