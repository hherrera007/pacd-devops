import os

from aws_cdk import Duration, RemovalPolicy, SecretValue, aws_ec2 as ec2, aws_rds as rds
from constructs import Construct


class PacdPostgresDatabase(Construct):
    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.IVpc) -> None:
        super().__init__(scope, construct_id)

        # Explicit DB security group; no inbound rules are added by default.
        self.security_group = ec2.SecurityGroup(
            self,
            "PacdPostgresSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for the PACD PostgreSQL database.",
        )

        # Small public PostgreSQL instance for demo purposes.
        self.database = rds.DatabaseInstance(
            self,
            "PacdPostgresDatabase",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16_3,
            ),
            # Reads credentials from local environment variables, not Secrets Manager.
            credentials=rds.Credentials.from_password(
                username=os.getenv("DATABASE_USERNAME"),
                password=SecretValue.unsafe_plain_text(os.getenv("DATABASE_PASSWORD")),
            ),
            database_name=os.getenv("DATABASE_NAME", "pacd"),
            vpc=vpc,
            # Public subnet placement keeps laptop access simple for demos.
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC,
            ),
            security_groups=[self.security_group],
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE4_GRAVITON,
                ec2.InstanceSize.MICRO,
            ),
            allocated_storage=20,
            storage_type=rds.StorageType.GP3,
            multi_az=False,
            # Public IP may add cost; security group still controls access.
            publicly_accessible=True,
            backup_retention=Duration.days(0),
            delete_automated_backups=True,
            deletion_protection=False,
            # Allows stack deletion to remove the demo database.
            removal_policy=RemovalPolicy.DESTROY,
        )

    def allow_connections_from(self, peer: ec2.ISecurityGroup, tag: str = "loader") -> None:
        # Allows only the provided security group to connect to PostgreSQL.
        self.security_group.add_ingress_rule(
            peer=peer,
            connection=ec2.Port.tcp(5432),
            description=f"Allow PostgreSQL access from the demo {tag} Lambda.",
        )
