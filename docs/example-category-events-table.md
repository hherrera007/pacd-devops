# Example Category Events Table

The `category_events` table stores category click events after Firehose writes them to S3 and the loader Lambda inserts them into PostgreSQL.

This table is used by the analytics dashboard.

```sql
CREATE TABLE category_events (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(50) NOT NULL,
    category VARCHAR(100) NOT NULL,
    event_time TIMESTAMPTZ NOT NULL,
    source_ip INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);
```

## Notes

- `source_ip` is nullable because the Lambda Function URL request metadata is not guaranteed in every invocation.
- `user_agent` is nullable for the same reason.
- `event_time` is the time when the click collector Lambda received the event.
- `created_at` is the database insertion time.
