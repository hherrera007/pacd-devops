# Welcome to PACD Stack

This repository contains the AWS CDK Python project for the PACD stack.

## Prerequisites

- Python 3.10 or later
- Node.js and npm
- AWS CDK Toolkit
- AWS CLI version 2
- Access to an AWS account

Install the AWS CDK Toolkit if it is not already available:

```bash
npm install -g aws-cdk
cdk --version
```

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

## Example Data

- Example ventas table: [docs/example-ventas-table.md](docs/example-ventas-table.md)

## Cost References

- VPC cost notes: [docs/vpc-costs.md](docs/vpc-costs.md)
- S3 cost notes: [docs/s3-costs.md](docs/s3-costs.md)
- Lambda S3 CSV mover cost notes: [docs/lambda-s3-costs.md](docs/lambda-s3-costs.md)
- RDS PostgreSQL cost notes: [docs/rds-costs.md](docs/rds-costs.md)
- Security groups cost notes: [docs/security-groups-costs.md](docs/security-groups-costs.md)
- AWS VPC pricing: <https://aws.amazon.com/vpc/pricing/>
- AWS S3 pricing: <https://aws.amazon.com/s3/pricing/>
- AWS Lambda pricing: <https://aws.amazon.com/lambda/pricing/>
- AWS RDS for PostgreSQL pricing: <https://aws.amazon.com/rds/postgresql/pricing/>
