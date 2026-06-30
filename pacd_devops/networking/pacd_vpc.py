from aws_cdk import aws_ec2 as ec2
from constructs import Construct


class PacdVpc(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        self.vpc = ec2.Vpc(
            self,
            # Logical ID for the VPC construct.
            "PacdVpc",
            # Main IPv4 range for this VPC.
            ip_addresses=ec2.IpAddresses.cidr("10.1.0.0/16"),
            # Creates subnets in two Availability Zones.
            max_azs=2,
            # Keeps the VPC free of NAT Gateway hourly charges.
            nat_gateways=0,
            # Avoids CDK's helper Lambda for the default security group.
            restrict_default_security_group=False,
            # Defines the subnet groups CDK creates.
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    # Public subnet group name.
                    name="public",
                    # Routes outbound traffic through the Internet Gateway.
                    subnet_type=ec2.SubnetType.PUBLIC,
                    # Each public subnet uses a /24 block.
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    # Private subnet group name.
                    name="private-isolated",
                    # No route to the internet or NAT Gateway.
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    # Each isolated subnet uses a /24 block.
                    cidr_mask=24,
                ),
            ],
        )
