# VPC Cost Notes

This stack creates a VPC with CIDR `10.1.0.0/16` and `nat_gateways=0`.

## Resources Created

The CDK VPC construct creates networking resources such as:

- VPC
- public subnets
- private isolated subnets
- route tables
- internet gateway
- S3 Gateway Endpoint
- subnet route table associations

These resources do not have a direct hourly charge by themselves.

## NAT Gateway Cost

This VPC creates `0` NAT gateways, so the NAT Gateway cost is `$0`.

If a NAT Gateway is added later, AWS charges:

- NAT Gateway hourly charge: about `$0.045` per NAT Gateway-hour in common US regions
- NAT Gateway data processing: about `$0.045` per GB processed
- Standard data transfer charges may also apply
- Public IPv4 charge for the Elastic IP attached to the NAT Gateway: `$0.005` per hour

Approximate monthly cost for one NAT Gateway running 24/7 for 30 days, before traffic:

```text
720 hours x $0.045 = $32.40
720 hours x $0.005 public IPv4 = $3.60
Base monthly total per NAT Gateway = $36.00 plus data processing and transfer
```

## Public IPv4 Cost

Public subnets do not create billable public IPv4 addresses by themselves.

AWS charges for each public IPv4 address used by resources in the account:

```text
$0.005 per public IPv4 address per hour
720 hours x $0.005 = $3.60 per month per public IPv4 address
```

Examples of resources that can create public IPv4 cost:

- EC2 instance with auto-assigned public IPv4: about `$3.60` per month per public IP
- Elastic IP attached to a NAT Gateway: about `$3.60` per month per public IP
- Elastic IP attached to an EC2 instance: about `$3.60` per month per public IP
- Idle Elastic IP not attached to a resource: about `$3.60` per month per public IP
- Public load balancer IPs: about `$3.60` per month per public IP, in addition to load balancer charges

## Current Expected Monthly Network Cost

With this VPC alone and `0` NAT gateways:

```text
VPC, subnets, route tables, internet gateway: $0
NAT Gateways: $0
Public IPv4 addresses created by this VPC alone: $0
```

The expected direct monthly network cost is `$0`, unless resources are later added that use NAT Gateways, public IPv4 addresses, traffic processing, or data transfer.

Pricing reference: <https://aws.amazon.com/vpc/pricing/>
