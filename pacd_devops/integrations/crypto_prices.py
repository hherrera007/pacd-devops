import os

from aws_cdk import BundlingOptions, DockerImage, Duration, RemovalPolicy, aws_iam as iam, aws_lambda as lambda_, aws_logs as logs, aws_s3 as s3
from constructs import Construct


class CryptoPrices(Construct):
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
            "CryptoPricesLogGroup",
            log_group_name="/aws/lambda/crypto-prices",
            # Keeps demo price polling logs short-lived.
            retention=logs.RetentionDays.ONE_DAY,
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.function = lambda_.Function(
            self,
            "CryptoPricesFunction",
            function_name="crypto-prices",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="app.handler",
            code=lambda_.Code.from_asset(
                "lambda_functions/crypto_prices",
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
            timeout=Duration.seconds(15),
            memory_size=128,
            log_group=log_group,
            # No VPC; the Lambda needs public internet for Binance.
            environment={
                "BINANCE_PRICE_URL": os.getenv("BINANCE_PRICE_URL", "https://data-api.binance.vision/api/v3/ticker/price"),
                "BUCKET_NAME": bucket.bucket_name,
                "CACHE_KEY": "crypto-prices/latest.json",
                "CACHE_TTL_SECONDS": "10",
            },
        )

        # Lets the Lambda share one 10-second price cache across all clients.
        bucket.grant_read_write(self.function)

        self.function_url = self.function.add_function_url(
            # Public demo endpoint; no AWS auth required.
            auth_type=lambda_.FunctionUrlAuthType.NONE,
            cors=lambda_.FunctionUrlCorsOptions(
                allowed_methods=[lambda_.HttpMethod.GET],
                allowed_origins=["*"],
                allowed_headers=["content-type"],
            ),
        )

        # Public permissions required for unauthenticated Function URL calls.
        self.function.add_permission(
            "CryptoPricesUrlInvokePermission",
            principal=iam.AnyPrincipal(),
            action="lambda:InvokeFunctionUrl",
            function_url_auth_type=lambda_.FunctionUrlAuthType.NONE,
        )
        self.function.add_permission(
            "CryptoPricesFunctionInvokePermission",
            principal=iam.AnyPrincipal(),
            action="lambda:InvokeFunction",
        )
