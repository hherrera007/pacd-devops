import os

from aws_cdk import BundlingOptions, DockerImage, Duration, RemovalPolicy, aws_iam as iam, aws_lambda as lambda_, aws_logs as logs, aws_s3 as s3
from constructs import Construct


class ExternalApiEnrichment(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        bucket: s3.IBucket,
    ) -> None:
        super().__init__(scope, construct_id)

        log_group = logs.LogGroup(
            self,
            "ExternalApiEnrichmentLogGroup",
            log_group_name="/aws/lambda/external-api-enrichment",
            # Keeps demo enrichment logs short-lived.
            retention=logs.RetentionDays.ONE_DAY,
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.function = lambda_.Function(
            self,
            "ExternalApiEnrichmentFunction",
            function_name="external-api-enrichment",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="app.handler",
            code=lambda_.Code.from_asset(
                "lambda_functions/external_api_enrichment",
                bundling=BundlingOptions(
                    # Packages requests with the Lambda asset.
                    image=DockerImage.from_registry("python:3.12-slim"),
                    command=[
                        "bash",
                        "-c",
                        "pip install -r requirements.txt -t /asset-output && cp -R /asset-input/. /asset-output/",
                    ],
                ),
            ),
            timeout=Duration.seconds(20),
            memory_size=128,
            log_group=log_group,
            # No VPC here; the Lambda needs public internet for external APIs.
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "OUTPUT_PREFIX": "external-api-enrichment/",
                "PRODUCTS_API_ONE_URL": os.getenv("PRODUCTS_API_ONE_URL", "https://fakestoreapi.com/products"),
                "PRODUCTS_API_TWO_URL": os.getenv("PRODUCTS_API_TWO_URL", "https://api.escuelajs.co/api/v1/products"),
            },
        )

        # Lets the Lambda store raw and comparison API payloads.
        bucket.grant_put(self.function)

        self.function_url = self.function.add_function_url(
            # Public demo endpoint; no AWS auth required.
            auth_type=lambda_.FunctionUrlAuthType.NONE,
            cors=lambda_.FunctionUrlCorsOptions(
                allowed_methods=[lambda_.HttpMethod.POST],
                allowed_origins=["*"],
                allowed_headers=["content-type"],
            ),
        )

        # Public permissions required for unauthenticated Function URL calls.
        self.function.add_permission(
            "ExternalApiEnrichmentUrlInvokePermission",
            principal=iam.AnyPrincipal(),
            action="lambda:InvokeFunctionUrl",
            function_url_auth_type=lambda_.FunctionUrlAuthType.NONE,
        )
        self.function.add_permission(
            "ExternalApiEnrichmentFunctionInvokePermission",
            principal=iam.AnyPrincipal(),
            action="lambda:InvokeFunction",
        )
