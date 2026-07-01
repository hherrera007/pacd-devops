# Lambda S3 CSV Mover Cost Notes

This stack defines a Lambda function that runs when a `.csv` file is uploaded to the `inbound/` prefix of the `files.pacd.edu` S3 bucket.

## Current Behavior

When an object like this is created:

```text
inbound/example.csv
```

The Lambda copies it to:

```text
outbound/example.csv
```

Then it deletes the original `inbound/` object.

## Cost Drivers

Lambda charges are based on:

- invocation requests
- execution duration
- configured memory

The function uses:

```text
Memory: 128 MB
Timeout: 30 seconds
Trigger: S3 object-created event for inbound/*.csv
```

AWS Lambda pricing includes one million requests and 400,000 GB-seconds per month in the free tier. On pay as you go, small demo usage should usually be very low cost.

## Execution Price Example

For this function, memory is set to `128 MB`, which is `0.125 GB`.

Outside the free tier, common Lambda prices in `us-east-1` are:

```text
Requests: $0.20 per 1,000,000 requests
Duration: $0.0000166667 per GB-second
```

Approximate cost for one execution that runs for `1 second`:

```text
Request: $0.20 / 1,000,000 = $0.00000020
Duration: 0.125 GB x 1 second x $0.0000166667 = $0.00000208
Total per 1-second execution: about $0.00000228
```

Example monthly costs outside the free tier:

```text
1,000 executions at 1 second each: about $0.0023
10,000 executions at 1 second each: about $0.0228
100,000 executions at 1 second each: about $0.228
```

If executions stay inside the Lambda free tier, the Lambda execution cost is `$0`.

## CloudWatch Log Group Cost

Lambda creates a CloudWatch Log Group when the function writes logs.

The log group existing by itself has no meaningful cost. CloudWatch Logs cost comes from:

- log data ingested
- log data stored
- log data scanned by Logs Insights queries

Common `us-east-1` reference prices:

```text
Free tier: 5 GB per month across ingestion, archive storage, and Logs Insights scanned data
Log ingestion after free tier: about $0.50 per GB
Log archive storage after free tier: about $0.03 per GB-month
```

Example for small demo logs:

```text
1 MB logs/month = 0.001 GB
Ingestion: 0.001 GB x $0.50 = $0.0005
Storage: 0.001 GB x $0.03 = $0.00003 per month
```

So for this demo Lambda, CloudWatch Logs should usually be `$0` or near `$0`, unless the function logs heavily or logs are queried frequently.

S3 also charges for the copy and delete operations:

- copy uses a PUT/COPY request
- delete requests are free
- storage cost depends on the size and lifetime of the files

## Security and Access

The Lambda receives read/write permissions only for the S3 bucket. It is not placed inside the VPC and does not need database access.

Pricing references:

- <https://aws.amazon.com/lambda/pricing/>
- <https://aws.amazon.com/cloudwatch/pricing/>
- <https://aws.amazon.com/s3/pricing/>
