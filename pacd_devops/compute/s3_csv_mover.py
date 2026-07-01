import os

from aws_cdk import Duration, RemovalPolicy, aws_ec2 as ec2, aws_lambda as lambda_, aws_logs as logs, aws_rds as rds, aws_s3 as s3, aws_s3_notifications as s3n
from constructs import Construct


class S3CsvMover(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        bucket: s3.IBucket,
        database: rds.IDatabaseInstance,
        vpc: ec2.IVpc,
    ) -> None:
        super().__init__(scope, construct_id)

        self.security_group = ec2.SecurityGroup(
            self,
            "S3CsvMoverSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for the CSV loader Lambda.",
        )

        log_group = logs.LogGroup(
            self,
            "S3CsvMoverLogGroup",
            # Deletes Lambda logs after one day to avoid log buildup.
            retention=logs.RetentionDays.ONE_DAY,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Lambda that validates incoming CSV files and loads valid rows into Postgres.
        self.function = lambda_.Function(
            self,
            "S3CsvMoverFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="app.handler",
            code=lambda_.Code.from_asset("lambda_functions/s3_csv_mover"),
            timeout=Duration.seconds(30),
            memory_size=128,
            log_group=log_group,
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
            security_groups=[self.security_group],
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "INBOUND_PREFIX": "inbound/",
                "OUTBOUND_PREFIX": "outbound/",
                "DATABASE_HOST": database.db_instance_endpoint_address,
                "DATABASE_PORT": database.db_instance_endpoint_port,
                "DATABASE_NAME": os.getenv("DATABASE_NAME", "pacd"),
                "DATABASE_USERNAME": os.getenv("DATABASE_USERNAME", ""),
                "DATABASE_PASSWORD": os.getenv("DATABASE_PASSWORD", ""),
            },
        )

        # Allows the Lambda to read CSV files and write invalid-record reports.
        bucket.grant_read_write(self.function)
        # Triggers only for new CSV files under inbound/.
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.function),
            s3.NotificationKeyFilter(prefix="inbound/", suffix=".csv"),
        )
