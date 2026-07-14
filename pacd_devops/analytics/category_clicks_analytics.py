import os

from aws_cdk import BundlingOptions, DockerImage, Duration, RemovalPolicy, aws_ec2 as ec2, aws_iam as iam, aws_lambda as lambda_, aws_logs as logs, aws_rds as rds
from constructs import Construct


class CategoryClicksAnalytics(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        database: rds.IDatabaseInstance = None,
        vpc: ec2.IVpc,
    ) -> None:
        super().__init__(scope, construct_id)

        # Security group used by the analytics Lambda to reach PostgreSQL.
        self.security_group = ec2.SecurityGroup(
            self,
            "CategoryClicksAnalyticsSecurityGroup",
            vpc=vpc,
            allow_all_outbound=True,
            description="Security group for category clicks analytics Lambda.",
        )

        log_group = logs.LogGroup(
            self,
            "CategoryClicksAnalyticsLogGroup",
            log_group_name="/aws/lambda/category-clicks-analytics",
            # Keeps demo analytics logs short-lived.
            retention=logs.RetentionDays.ONE_DAY,
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.function = lambda_.Function(
            self,
            "CategoryClicksAnalyticsFunction",
            function_name="category-clicks-analytics",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="app.handler",
            code=lambda_.Code.from_asset(
                "lambda_functions/category_clicks_analytics",
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
            timeout=Duration.seconds(15),
            memory_size=128,
            log_group=log_group,
            vpc=vpc,
            # No NAT needed; Lambda only reads RDS inside this VPC.
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
            ),
            security_groups=[self.security_group],
            environment={
                # Database values used by the analytics Lambda.
                "DATABASE_HOST": database.db_instance_endpoint_address if database else "",
                "DATABASE_PORT": database.db_instance_endpoint_port if database else "",
                "DATABASE_NAME": os.getenv("DATABASE_NAME", "pacd"),
                "DATABASE_USERNAME": os.getenv("DATABASE_USERNAME", ""),
                "DATABASE_PASSWORD": os.getenv("DATABASE_PASSWORD", ""),
            },
        )

        self.function_url = self.function.add_function_url(
            # Public demo endpoint for the static dashboard.
            # CORS headers are returned by the Lambda code.
            auth_type=lambda_.FunctionUrlAuthType.NONE,
        )

        # Public permissions required for unauthenticated Function URL calls.
        self.function.add_permission(
            "CategoryClicksAnalyticsUrlInvokePermission",
            principal=iam.AnyPrincipal(),
            action="lambda:InvokeFunctionUrl",
            function_url_auth_type=lambda_.FunctionUrlAuthType.NONE,
        )
        self.function.add_permission(
            "CategoryClicksAnalyticsFunctionInvokePermission",
            principal=iam.AnyPrincipal(),
            action="lambda:InvokeFunction",
        )
