from aws_cdk import (
    CfnOutput,
    # Duration,
    Stack, Tags,
    # aws_sqs as sqs,
)
from constructs import Construct

from pacd_devops.alarms.monthly_budget_alarm import MonthlyBudgetAlarm
from pacd_devops.compute.csv_upload_url import CsvUploadUrl
from pacd_devops.compute.s3_csv_mover import S3CsvMover
from pacd_devops.constants import TAG_KEYS, MODULES
from pacd_devops.database.pacd_postgres_database import PacdPostgresDatabase
from pacd_devops.networking.pacd_vpc import PacdVpc
from pacd_devops.storage.pacd_files_bucket import PacdFilesBucket


class PacdDevopsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Sends an email when monthly AWS cost approaches the budget limit.
        monthly_budget = MonthlyBudgetAlarm(self, "MonthlyBudgetAlarm")
        Tags.of(monthly_budget).add(TAG_KEYS.MODULE, MODULES.BILLING)

        # Creates the low-cost network foundation for the stack.
        pacd_vpc = PacdVpc(self, "PacdVpc")
        Tags.of(pacd_vpc).add(TAG_KEYS.MODULE, MODULES.NETWORKING)

        # Stores uploaded files used by the demo workflow.
        files_bucket = PacdFilesBucket(
            self,
            "PacdFilesBucket",
            bucket_name="files.pacd.edu",
        )
        Tags.of(files_bucket).add(TAG_KEYS.MODULE, MODULES.STORAGE)

        # Small database for demos.
        postgres_database = PacdPostgresDatabase(
            self,
            "PacdPostgresDatabase",
            vpc=pacd_vpc.vpc,
        )
        Tags.of(postgres_database).add(TAG_KEYS.MODULE, MODULES.DATABASE)

        # Validates CSV files and writes invalid rows to S3.
        csv_mover = S3CsvMover(
            self,
            "S3CsvMover",
            bucket=files_bucket.bucket,
            database=postgres_database.database,
            vpc=pacd_vpc.vpc,
        )
        postgres_database.allow_connections_from(csv_mover.security_group)
        Tags.of(csv_mover).add(TAG_KEYS.MODULE, MODULES.COMPUTE)

        # Public demo URL that uploads CSV files into S3 inbound/.
        csv_upload_url = CsvUploadUrl(
            self,
            "CsvUploadUrl",
            bucket=files_bucket.bucket,
        )
        Tags.of(csv_upload_url).add(TAG_KEYS.MODULE, MODULES.COMPUTE)

        CfnOutput(
            self,
            "CsvUploadFunctionUrl",
            # Prints the public upload URL after deployment.
            value=csv_upload_url.function_url.url,
            description="Public demo URL for uploading CSV files to S3 inbound/.",
        )


