# RDS PostgreSQL Cost Notes

This stack defines one Amazon RDS for PostgreSQL database.

## Current Database Configuration

The database is configured with:

- engine: PostgreSQL `16.3`
- instance class: `db.t4g.micro`
- storage: `20 GiB` gp3
- deployment: Single-AZ
- subnets: public subnets
- public accessibility: enabled
- backups: disabled
- deletion protection: disabled
- removal policy: destroy
- credentials: hardcoded username and password, not Secrets Manager

## Security Group

CDK can create a security group automatically for an RDS instance, but this stack creates one explicitly.

The database security group allows inbound PostgreSQL traffic on port `5432` only from the CSV loader Lambda security group.

Do not add public `0.0.0.0/0` database access unless this is strictly needed for a temporary demo.

## Expected Cost

RDS is not free just because the database is idle. Billing starts when the DB instance is created and available.

Main cost drivers are:

- DB instance hours
- allocated storage
- backup storage
- data transfer
- extra CPU credits if burstable CPU use exceeds baseline

Approximate pay-as-you-go estimate for a small Single-AZ `db.t4g.micro` with `20 GiB` storage in `us-east-1`:

```text
DB instance hours: roughly $10-$15 per month
20 GiB gp3 storage: roughly $2-$3 per month
Estimated baseline total without public IPv4: roughly $12-$18 per month
```

Because this demo database is in public subnets with `publicly_accessible=True`, AWS may attach a public IPv4 address to the RDS instance.

```text
Public IPv4: $0.005 per hour, about $3.60 per month
Estimated baseline total with public IPv4: roughly $16-$22 per month
```

This estimate excludes data transfer, snapshots, extra backup storage, and burst CPU credit charges.

## Secrets Manager Cost Avoided

This database intentionally does not create an AWS Secrets Manager secret.

If Secrets Manager is used later, common pricing is:

```text
Secret storage: about $0.40 per secret per month
API calls: about $0.05 per 10,000 calls
```

Hardcoding credentials avoids the Secrets Manager charge, but it is weaker security. For production, use Secrets Manager even with the extra cost.

Pricing references:

- <https://aws.amazon.com/rds/postgresql/pricing/>
- <https://aws.amazon.com/secrets-manager/pricing/>
