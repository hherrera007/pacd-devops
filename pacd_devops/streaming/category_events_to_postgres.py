import os

from aws_cdk import BundlingOptions, DockerImage, Duration, RemovalPolicy, aws_ec2 as ec2, aws_lambda as lambda_, aws_logs as logs, aws_rds as rds, aws_s3 as s3, aws_s3_notifications as s3n
from constructs import Construct


class CategoryEventsToPostgres(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        bucket: s3.IBucket,
        database: rds.IDatabaseInstance,
        vpc: ec2.IVpc,
    ) -> None:
        super().__init__(scope, construct_id)

        # Security group used by the loader Lambda to reach PostgreSQL.
        self.security_group = ec2.SecurityGroup(
            self,
            "CategoryEventsToPostgresSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for category events loader Lambda.",
        )

        log_group = logs.LogGroup(
            self,
            "CategoryEventsToPostgresLogGroup",
            log_group_name="/aws/lambda/category-events-to-postgres",
            # Keeps demo loader logs short-lived.
            retention=logs.RetentionDays.ONE_DAY,
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.function = lambda_.Function(
            self,
            "CategoryEventsToPostgresFunction",
            function_name="category-events-to-postgres",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="app.handler",
            code=lambda_.Code.from_asset(
                "lambda_functions/category_events_to_postgres",
                bundling=BundlingOptions(
                    # Packages pg8000 with the Lambda asset.
                    image=DockerImage.from_registry("python:3.12-slim"),
                    command=[
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -R /asset-input/. /asset-output/",
                    ],
                ),
            ),
            timeout=Duration.seconds(30),
            memory_size=128,
            log_group=log_group,
            vpc=vpc,
            # No NAT needed; Lambda only reaches RDS inside this VPC.
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
            security_groups=[self.security_group],
            environment={
                # Database values used by the loader Lambda.
                "DATABASE_HOST": database.db_instance_endpoint_address,
                "DATABASE_PORT": database.db_instance_endpoint_port,
                "DATABASE_NAME": os.getenv("DATABASE_NAME", "pacd"),
                "DATABASE_USERNAME": os.getenv("DATABASE_USERNAME", ""),
                "DATABASE_PASSWORD": os.getenv("DATABASE_PASSWORD", ""),
            },
        )

        bucket.grant_read(self.function)
        # Invokes the loader when Firehose writes a new event file.
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.function),
            # Runs only for delivered Firehose event files.
            s3.NotificationKeyFilter(prefix="category-events/"),
        )
