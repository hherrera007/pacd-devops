from aws_cdk import Duration, RemovalPolicy, SecretValue, aws_ec2 as ec2, aws_rds as rds
from constructs import Construct


class PacdPostgresDatabase(Construct):
    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.IVpc) -> None:
        super().__init__(scope, construct_id)

        self.security_group = ec2.SecurityGroup(
            self,
            "PacdPostgresSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for the PACD PostgreSQL database.",
        )

        self.database = rds.DatabaseInstance(
            self,
            "PacdPostgresDatabase",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_16_3,
            ),
            credentials=rds.Credentials.from_password(
                username="pacd_admin",
                password=SecretValue.unsafe_plain_text("PacdDevPassw0rd!"),
            ),
            database_name="pacd",
            vpc=vpc,
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
            publicly_accessible=True,
            backup_retention=Duration.days(0),
            delete_automated_backups=True,
            deletion_protection=False,
            removal_policy=RemovalPolicy.DESTROY,
        )
