from aws_cdk import Duration, RemovalPolicy, aws_iam as iam, aws_kinesisfirehose as firehose, aws_lambda as lambda_, aws_logs as logs, aws_s3 as s3
from constructs import Construct


class CategoryEventsStream(Construct):
    def __init__(self, scope: Construct, construct_id: str, bucket_name: str) -> None:
        super().__init__(scope, construct_id)

        self.bucket = s3.Bucket(
            self,
            "CategoryEventsBucket",
            # Stores category click events delivered by Firehose.
            bucket_name=bucket_name,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            enforce_ssl=True,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        firehose_role = iam.Role(
            self,
            "CategoryEventsFirehoseRole",
            # Allows Firehose to write event files to S3.
            assumed_by=iam.ServicePrincipal("firehose.amazonaws.com"),
        )

        firehose_role.add_to_policy(
            iam.PolicyStatement(
                # Lets Firehose inspect the destination bucket before writing.
                actions=[
                    "s3:AbortMultipartUpload",
                    "s3:GetBucketLocation",
                    "s3:ListBucket",
                    "s3:ListBucketMultipartUploads",
                ],
                resources=[self.bucket.bucket_arn],
            )
        )
        firehose_role.add_to_policy(
            iam.PolicyStatement(
                # Lets Firehose create event objects in the bucket.
                actions=["s3:PutObject"],
                resources=[self.bucket.arn_for_objects("*")],
            )
        )

        self.delivery_stream = firehose.CfnDeliveryStream(
            self,
            "CategoryEventsDeliveryStream",
            delivery_stream_name="pacd-category-events",
            # Lambda sends records directly to this delivery stream.
            delivery_stream_type="DirectPut",
            extended_s3_destination_configuration=firehose.CfnDeliveryStream.ExtendedS3DestinationConfigurationProperty(
                bucket_arn=self.bucket.bucket_arn,
                role_arn=firehose_role.role_arn,
                buffering_hints=firehose.CfnDeliveryStream.BufferingHintsProperty(
                    # Low buffering delay for demos.
                    interval_in_seconds=60,
                    size_in_m_bs=1,
                ),
                compression_format="UNCOMPRESSED",
                # Partitions delivered files by event date.
                prefix="category-events/year=!{timestamp:yyyy}/month=!{timestamp:MM}/day=!{timestamp:dd}/",
                error_output_prefix="category-events-errors/",
            ),
        )

        log_group = logs.LogGroup(
            self,
            "CategoryEventCollectorLogGroup",
            log_group_name="/aws/lambda/category-event-collector",
            # Keeps demo collector logs short-lived.
            retention=logs.RetentionDays.ONE_DAY,
            removal_policy=RemovalPolicy.DESTROY,
        )

        self.function = lambda_.Function(
            self,
            "CategoryEventCollectorFunction",
            function_name="category-event-collector",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="app.handler",
            code=lambda_.Code.from_asset("lambda_functions/category_event_collector"),
            timeout=Duration.seconds(10),
            memory_size=128,
            log_group=log_group,
            environment={
                # Tells the Lambda where to send category events.
                "DELIVERY_STREAM_NAME": self.delivery_stream.ref,
            },
        )

        self.function.add_to_role_policy(
            iam.PolicyStatement(
                # Allows the collector Lambda to send records to Firehose.
                actions=["firehose:PutRecord"],
                resources=[self.delivery_stream.attr_arn],
            )
        )

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
            "CategoryEventUrlInvokePermission",
            principal=iam.AnyPrincipal(),
            action="lambda:InvokeFunctionUrl",
            function_url_auth_type=lambda_.FunctionUrlAuthType.NONE,
        )
        self.function.add_permission(
            "CategoryEventFunctionInvokePermission",
            principal=iam.AnyPrincipal(),
            action="lambda:InvokeFunction",
        )
