# Category Events Firehose Cost Notes

This stack creates a public Lambda Function URL that receives category click events, sends them to Amazon Data Firehose, and stores the delivered files in S3.

## Resources Created

| Resource | Purpose | Cost behavior |
| --- | --- | --- |
| Lambda Function URL | Public HTTPS endpoint for category events | No direct Function URL charge |
| Lambda function | Receives the category and calls Firehose | Charged by requests and duration |
| CloudWatch log group | Stores Lambda logs | Charged by log ingestion and retained storage |
| Firehose delivery stream | Buffers events and delivers them to S3 | Charged by ingested GB |
| S3 bucket | Stores delivered event files | Charged by storage and requests |
| Bucket auto-delete helper | Empties the demo bucket during stack deletion | Tiny Lambda/custom resource cost only when used |
| IAM role/policies | Permissions for Lambda and Firehose | No direct charge |

## Firehose Cost

For Direct PUT delivery to S3, Amazon Data Firehose charges for ingested data volume. AWS bills Direct PUT ingestion in 5 KB increments per record.

For small demo events, the cost is usually tiny because each click event is only a small JSON record. There is no Firehose hourly base charge for this simple Direct PUT to S3 design.

Optional Firehose features can add cost, but they are not enabled here:

- VPC delivery
- Dynamic partitioning
- Format conversion to Parquet or ORC
- Lambda data transformation inside Firehose

Pricing reference: <https://aws.amazon.com/firehose/pricing/>

## S3 Cost

Firehose writes event files into an S3 bucket. S3 charges apply for:

- Stored data
- PUT requests created by Firehose
- GET/LIST requests when reading the files

Pricing reference: <https://aws.amazon.com/s3/pricing/>

## Lambda and Logs Cost

Each click invokes the collector Lambda once. Lambda charges are based on request count and execution duration.

The Lambda log group is configured with one-day retention to keep demo log storage small.

Pricing references:

- <https://aws.amazon.com/lambda/pricing/>
- <https://aws.amazon.com/cloudwatch/pricing/>

## Data Delay

Firehose buffers records before writing to S3. This stack uses a low demo buffer of 60 seconds or 1 MiB, so events will not appear in S3 instantly.
