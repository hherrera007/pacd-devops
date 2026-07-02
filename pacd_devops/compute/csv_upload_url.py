from aws_cdk import Duration, RemovalPolicy, aws_iam as iam, aws_lambda as lambda_, aws_logs as logs, aws_s3 as s3
from constructs import Construct


class CsvUploadUrl(Construct):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        bucket: s3.IBucket,
    ) -> None:
        super().__init__(scope, construct_id)

        log_group = logs.LogGroup(
            self,
            "CsvUploadUrlLogGroup",
            log_group_name="/aws/lambda/csv-upload-url",
            # Keeps demo upload logs short-lived.
            retention=logs.RetentionDays.ONE_DAY,
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Public demo Lambda that writes request bodies to S3 inbound/.
        self.function = lambda_.Function(
            self,
            "CsvUploadUrlFunction",
            function_name="csv-upload-url",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="app.handler",
            code=lambda_.Code.from_asset("lambda_functions/csv_upload_url"),
            timeout=Duration.seconds(10),
            memory_size=128,
            log_group=log_group,
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "INBOUND_PREFIX": "inbound/",
            },
        )

        # Lets the upload Lambda write CSV files into the bucket.
        bucket.grant_put(self.function)

        # Creates a public HTTPS endpoint without API Gateway.
        self.function_url = self.function.add_function_url(
            auth_type=lambda_.FunctionUrlAuthType.NONE,
            cors=lambda_.FunctionUrlCorsOptions(
                allowed_methods=[lambda_.HttpMethod.POST],
                allowed_origins=["*"],
                allowed_headers=["content-type"],
            ),
        )

        # Public permissions required for unauthenticated Function URL calls.
        self.function.add_permission(
            "CsvUploadUrlInvokePermission",
            principal=iam.AnyPrincipal(),
            action="lambda:InvokeFunctionUrl",
            function_url_auth_type=lambda_.FunctionUrlAuthType.NONE,
        )

        self.function.add_permission(
            "CsvUploadFunctionInvokePermission",
            principal=iam.AnyPrincipal(),
            action="lambda:InvokeFunction",
        )
