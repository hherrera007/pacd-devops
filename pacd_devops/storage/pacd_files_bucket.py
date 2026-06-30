from aws_cdk import RemovalPolicy, aws_s3 as s3
from constructs import Construct


class PacdFilesBucket(Construct):
    def __init__(self, scope: Construct, construct_id: str, bucket_name: str) -> None:
        super().__init__(scope, construct_id)

        self.bucket = s3.Bucket(
            self,
            "PacdFilesBucket",
            # Globally unique S3 bucket name.
            bucket_name=bucket_name,
            # Keeps the bucket private by default.
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            # Uses Amazon S3 managed encryption.
            encryption=s3.BucketEncryption.S3_MANAGED,
            # Rejects non-HTTPS requests.
            enforce_ssl=True,
            # Deletes the bucket when the stack removes this resource.
            removal_policy=RemovalPolicy.DESTROY,
            # Empties objects first so bucket deletion can succeed.
            auto_delete_objects=True,
        )
