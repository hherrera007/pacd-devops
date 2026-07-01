# Security Groups Cost Notes

Security groups do not have a direct hourly or monthly charge.

```text
Security group cost: $0
Security group rules cost: $0
Inbound rules cost: $0
Outbound rules cost: $0
```

You are correct: creating security groups and security group rules is free.

## Current Stack Usage

The stack creates an explicit security group for the PostgreSQL database:

```text
PacdPostgresSecurityGroup
```

The database security group currently has no inbound PostgreSQL rule. That means the security group itself costs `$0` and it does not allow public database access by default.

## What Can Still Create Cost

Security groups are free, but the resources attached to them may cost money.

Examples:

- RDS database attached to a security group: RDS instance and storage cost money.
- EC2 instance attached to a security group: EC2 instance, EBS, and public IPv4 may cost money.
- Load balancer attached to a security group: load balancer hours and traffic may cost money.

So the security group is `$0`; the protected resource is what may create cost.

## Default Security Group Note

Every VPC has a default security group. The VPC currently uses:

```python
restrict_default_security_group=False
```

That avoids CDK creating a helper Lambda to modify the VPC default security group. The default security group itself still has no direct cost.

Pricing reference: <https://aws.amazon.com/vpc/pricing/>
