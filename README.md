# Welcome to PACD Stack

This repository contains the AWS CDK Python project for the PACD stack.

## Prerequisites

- Python 3.10 or later
- Node.js and npm
- AWS CDK Toolkit
- AWS CLI version 2
- Docker Desktop or Docker Engine
- Access to an AWS account

Install the AWS CDK Toolkit if it is not already available:

```bash
npm install -g aws-cdk
cdk --version
```

Docker must be running before CDK commands that build Lambda assets. This stack uses Docker to package the `pg8000` PostgreSQL dependency into the S3 CSV mover Lambda.

## Install the AWS CLI

Install AWS CLI version 2 for your operating system.

### Windows

Download and run the official Windows MSI installer:

```text
https://awscli.amazonaws.com/AWSCLIV2.msi
```

Then open a new terminal and verify the installation:

```powershell
aws --version
```

### macOS

Download and run the official macOS package:

```text
https://awscli.amazonaws.com/AWSCLIV2.pkg
```

Then verify the installation:

```bash
aws --version
```

### Linux

Use the official AWS CLI installer:

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

For ARM-based Linux systems, use:

```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-aarch64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
aws --version
```

## Create a New AWS Account

To create a new AWS account:

1. Go to the AWS account creation page: <https://aws.amazon.com/resources/create-account/>
2. Enter the root user email address and AWS account name.
3. Verify the email address.
4. Create the root user password.
5. Add contact information.
6. Add a payment method.
7. Verify your phone number.
8. Choose an AWS Support plan.
9. Wait for account activation. AWS usually activates accounts within a few minutes, but it can take up to 24 hours.

After the account is active, enable MFA for the root user and avoid using the root user for day-to-day work.

## Configure an AWS SSO Profile

Use AWS IAM Identity Center credentials with a named CLI profile.

Replace `<MY_PROFILE>` with the profile name you want to use, for example `personal`:

```bash
aws configure sso --profile <MY_PROFILE>
```

The wizard will ask for values such as:

- SSO session name
- SSO start URL or issuer URL
- SSO region
- AWS account
- Permission set or role
- Default client region
- Default output format

When the browser opens, complete the AWS sign-in flow. If the browser does not open automatically, follow the URL and code shown in the terminal.

## Access Your AWS Profile

Sign in to the SSO profile:

```bash
aws sso login --profile <MY_PROFILE>
```

Confirm which AWS identity is active:

```bash
aws sts get-caller-identity --profile <MY_PROFILE>
```

Run AWS CLI commands with that profile:

```bash
aws s3 ls --profile <MY_PROFILE>
aws cloudformation list-stacks --profile <MY_PROFILE>
```

When you are done, you can sign out from cached SSO sessions:

```bash
aws sso logout
```

## Set Up the Project

Create and activate a Python virtual environment.

On macOS and Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Install the project dependencies:

```bash
pip install -r requirements.txt
```

## Configure the `.env` File

Create a `.env` file in the project root:

```text
AWS_ACCOUNT=<YOUR_AWS_ACCOUNT_ID>
AWS_REGION=us-east-1
BUDGET_ALERT_EMAIL=<YOUR_EMAIL>
DATABASE_USERNAME=pacd_admin
DATABASE_PASSWORD=<YOUR_DEMO_DATABASE_PASSWORD>
DATABASE_PORT=5432
DATABASE_NAME=pacd
FILES_BUCKET_NAME=<GLOBALLY_UNIQUE_FILES_BUCKET_NAME>
CATEGORY_EVENTS_BUCKET_NAME=<GLOBALLY_UNIQUE_CATEGORY_EVENTS_BUCKET_NAME>
EXTERNAL_API_BUCKET_NAME=<GLOBALLY_UNIQUE_EXTERNAL_API_BUCKET_NAME>
PRODUCTS_API_URL=https://api.escuelajs.co/api/v1/products
BINANCE_PRICE_URL=https://data-api.binance.vision/api/v3/ticker/price
```

Variable usage:

- `AWS_ACCOUNT`: AWS account where the CDK stack is deployed.
- `AWS_REGION`: AWS region for the stack, currently `us-east-1`.
- `BUDGET_ALERT_EMAIL`: email that receives the monthly budget alert.
- `DATABASE_USERNAME`: PostgreSQL demo user.
- `DATABASE_PASSWORD`: PostgreSQL demo password.
- `DATABASE_PORT`: PostgreSQL port, normally `5432`.
- `DATABASE_NAME`: PostgreSQL database name, currently `pacd`.
- `FILES_BUCKET_NAME`: S3 bucket used for CSV uploads and file processing.
- `CATEGORY_EVENTS_BUCKET_NAME`: S3 bucket where Firehose stores category click event files.
- `EXTERNAL_API_BUCKET_NAME`: S3 bucket where external API category cache payloads are stored.
- `PRODUCTS_API_URL`: external products API used by the enrichment Lambda.
- `BINANCE_PRICE_URL`: Binance ticker price endpoint used by the crypto prices Lambda.

S3 bucket names must be globally unique across all AWS accounts, not only inside your account. If a bucket name is already taken, deployment fails. A safe pattern is:

```text
files-pacd-<YOUR_AWS_ACCOUNT_ID>-<AWS_REGION>
category-events-pacd-<YOUR_AWS_ACCOUNT_ID>-<AWS_REGION>
external-api-pacd-<YOUR_AWS_ACCOUNT_ID>-<AWS_REGION>
```

## Optional PostgreSQL Flag

The PostgreSQL database is controlled by a code flag in [pacd_devops_stack.py](pacd_devops/pacd_devops_stack.py):

```python
ENABLE_POSTGRES_DATABASE = True
```

Set it to `False` to skip creating RDS. The database-dependent Lambdas still deploy, but their database host and port are empty, so database workflows will not work until PostgreSQL is enabled again.

## Bootstrap the Stack for the First Time

Before deploying a CDK stack into a new AWS account and region, bootstrap the AWS environment.

For the `personal` profile, run:

```bash
cdk bootstrap --profile personal
```

If you used a different profile name, replace `personal` with your profile:

```bash
cdk bootstrap --profile <MY_PROFILE>
```

## Useful CDK Commands

```bash
cdk ls --profile <MY_PROFILE>
cdk synth --profile <MY_PROFILE>
cdk diff --profile <MY_PROFILE>
cdk deploy --profile <MY_PROFILE>
cdk destroy --profile <MY_PROFILE>
```

Use `cdk synth` to generate and inspect the CloudFormation template before deploying changes.

## Upload a Demo CSV

After deployment, CloudFormation prints the public Lambda Function URL as:

```text
CsvUploadFunctionUrl
```

Upload a small CSV file to the S3 `inbound/` prefix:

```bash
curl -X POST \
  -H "Content-Type: text/csv" \
  --data-binary @example.csv \
  "<CsvUploadFunctionUrl>"
```

This demo URL is public and does not use API Gateway or authentication.

## Load External Products by Category

After deployment, CloudFormation prints the public external API enrichment Lambda Function URL as:

```text
ExternalApiEnrichmentFunctionUrl
```

The Lambda calls the external API configured by `PRODUCTS_API_URL`, filters products by category, and writes a category cache to:

```text
s3://<EXTERNAL_API_BUCKET_NAME>/external-api-enrichment/
```

More details: [docs/external-api-enrichment.md](docs/external-api-enrichment.md)

Static dashboard: [examples/external-api-enrichment-dashboard/README.md](examples/external-api-enrichment-dashboard/README.md)

## View Live Crypto Prices

After deployment, CloudFormation prints the public crypto prices Lambda Function URL as:

```text
CryptoPricesFunctionUrl
```

The Lambda reads Binance ticker prices for `BTCUSDT`, `ETHUSDT`, and `DOGEUSDT`, then shares a 10-second S3 cache across all clients.

Static dashboard: [examples/crypto-prices-dashboard/README.md](examples/crypto-prices-dashboard/README.md)

More details: [docs/crypto-prices.md](docs/crypto-prices.md)

## View Category Analytics

After deployment, CloudFormation prints the public analytics Lambda Function URL as:

```text
CategoryAnalyticsFunctionUrl
```

The static dashboard reads category click totals from the PostgreSQL `category_events` table and renders:

- A bar chart with total clicks per category.
- A line chart with click trends per category grouped every 60 seconds.
- A bar chart with the top 10 client IPs by click count.

Open [examples/category-analytics-dashboard/index.html](examples/category-analytics-dashboard/index.html) and replace:

```javascript
const analyticsUrl = "https://REPLACE_WITH_CATEGORY_ANALYTICS_FUNCTION_URL/";
```

with the deployed `CategoryAnalyticsFunctionUrl`.

### Browser CORS Behavior

The category click page sends the same JSON request format that the Lambda expects, but it does not `await` the response. The click message updates immediately while the request continues in the background.

The analytics dashboard must read JSON to draw the charts. The analytics Lambda returns CORS headers and allows `GET` and `OPTIONS` requests.

## Example Data

- Example ventas table: [docs/example-ventas-table.md](docs/example-ventas-table.md)
- Example category events table: [docs/example-category-events-table.md](docs/example-category-events-table.md)
- External API product cache demo: [docs/external-api-enrichment.md](docs/external-api-enrichment.md)
- External API product dashboard: [examples/external-api-enrichment-dashboard/README.md](examples/external-api-enrichment-dashboard/README.md)
- Crypto prices demo: [docs/crypto-prices.md](docs/crypto-prices.md)
- Crypto prices dashboard: [examples/crypto-prices-dashboard/README.md](examples/crypto-prices-dashboard/README.md)
- CSV upload HTML demo: [examples/csv-upload-demo/README.md](examples/csv-upload-demo/README.md)
- Category gallery event demo: [examples/category-gallery/README.md](examples/category-gallery/README.md)
- Category analytics dashboard: [examples/category-analytics-dashboard/README.md](examples/category-analytics-dashboard/README.md)

## Cost References

- VPC cost notes: [docs/vpc-costs.md](docs/vpc-costs.md)
- S3 cost notes: [docs/s3-costs.md](docs/s3-costs.md)
- Lambda S3 CSV mover cost notes: [docs/lambda-s3-costs.md](docs/lambda-s3-costs.md)
- Category events Firehose cost notes: [docs/category-events-firehose-costs.md](docs/category-events-firehose-costs.md)
- RDS PostgreSQL cost notes: [docs/rds-costs.md](docs/rds-costs.md)
- Security groups cost notes: [docs/security-groups-costs.md](docs/security-groups-costs.md)
- AWS VPC pricing: <https://aws.amazon.com/vpc/pricing/>
- AWS S3 pricing: <https://aws.amazon.com/s3/pricing/>
- AWS Lambda pricing: <https://aws.amazon.com/lambda/pricing/>
- AWS Data Firehose pricing: <https://aws.amazon.com/firehose/pricing/>
- AWS RDS for PostgreSQL pricing: <https://aws.amazon.com/rds/postgresql/pricing/>
