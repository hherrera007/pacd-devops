from aws_cdk import Duration, aws_lambda as lambda_, aws_s3 as s3, aws_s3_notifications as s3n
from constructs import Construct


class S3CsvMover(Construct):
    def __init__(self, scope: Construct, construct_id: str, bucket: s3.IBucket) -> None:
        super().__init__(scope, construct_id)

        # Lambda that moves uploaded CSV files from inbound/ to outbound/.
        self.function = lambda_.Function(
            self,
            "S3CsvMoverFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="app.handler",
            code=lambda_.Code.from_asset("lambda_functions/s3_csv_mover"),
            timeout=Duration.seconds(30),
            memory_size=128,
            environment={
                "BUCKET_NAME": bucket.bucket_name,
                "INBOUND_PREFIX": "inbound/",
                "OUTBOUND_PREFIX": "outbound/",
            },
        )

        # Allows the Lambda to copy and delete objects in this bucket.
        bucket.grant_read_write(self.function)
        # Triggers only for new CSV files under inbound/.
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.function),
            s3.NotificationKeyFilter(prefix="inbound/", suffix=".csv"),
        )
