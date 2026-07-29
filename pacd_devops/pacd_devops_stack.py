import os

from aws_cdk import (
    CfnOutput,
    # Duration,
    Stack, Tags,
    # aws_sqs as sqs,
)
from constructs import Construct

from pacd_devops.alarms.monthly_budget_alarm import MonthlyBudgetAlarm
from pacd_devops.analytics.category_clicks_analytics import CategoryClicksAnalytics
from pacd_devops.compute.csv_upload_url import CsvUploadUrl
from pacd_devops.compute.s3_csv_mover import S3CsvMover
from pacd_devops.constants import TAG_KEYS, MODULES
from pacd_devops.database.pacd_postgres_database import PacdPostgresDatabase
from pacd_devops.integrations.crypto_prices import CryptoPrices
from pacd_devops.integrations.external_api_enrichment import ExternalApiEnrichment
from pacd_devops.networking.pacd_vpc import PacdVpc
from pacd_devops.storage.pacd_files_bucket import PacdFilesBucket
from pacd_devops.streaming.category_events_to_postgres import CategoryEventsToPostgres
from pacd_devops.streaming.category_events_stream import CategoryEventsStream


# Set to False to skip only RDS; DB-dependent Lambdas still deploy with empty DB values.
ENABLE_POSTGRES_DATABASE = False


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
            bucket_name=os.getenv("FILES_BUCKET_NAME", "files.pacd.edu"),
        )
        Tags.of(files_bucket).add(TAG_KEYS.MODULE, MODULES.STORAGE)


        # Public demo URL that uploads CSV files into S3 inbound/.
        csv_upload_url = CsvUploadUrl(
            self,
            "CsvUploadUrl",
            bucket=files_bucket.bucket,
        )
        Tags.of(csv_upload_url).add(TAG_KEYS.MODULE, MODULES.COMPUTE)

        # Stores external API category cache payloads.
        external_api_bucket = PacdFilesBucket(
            self,
            "ExternalApiBucket",
            bucket_name=os.getenv("EXTERNAL_API_BUCKET_NAME", "external-api-pacd-demo"),
        )
        Tags.of(external_api_bucket).add(TAG_KEYS.MODULE, MODULES.STORAGE)

        # Calls one external API and caches category results in S3.
        external_api_enrichment = ExternalApiEnrichment(
            self,
            "ExternalApiEnrichment",
            bucket=external_api_bucket.bucket,
        )
        Tags.of(external_api_enrichment).add(TAG_KEYS.MODULE, MODULES.INTEGRATION)

        # Reads live crypto prices from Binance.
        crypto_prices = CryptoPrices(
            self,
            "CryptoPrices",
            bucket=external_api_bucket.bucket,
        )
        Tags.of(crypto_prices).add(TAG_KEYS.MODULE, MODULES.INTEGRATION)

        # Streams category click events to S3 through Firehose.
        category_events_stream = CategoryEventsStream(
            self,
            "CategoryEventsStream",
            bucket_name=os.getenv("CATEGORY_EVENTS_BUCKET_NAME", "category-events.pacd.edu"),
        )
        Tags.of(category_events_stream).add(TAG_KEYS.MODULE, MODULES.STREAMING)

        postgres_database = None

        if ENABLE_POSTGRES_DATABASE:
            # Small database for demos.
            postgres_database = PacdPostgresDatabase(
                self,
                "PacdPostgresDatabase",
                vpc=pacd_vpc.vpc,
            )
            Tags.of(postgres_database).add(TAG_KEYS.MODULE, MODULES.DATABASE)

        # Validates CSV files and inserts valid rows into PostgreSQL when enabled.
        csv_mover = S3CsvMover(
            self,
            "S3CsvMover",
            bucket=files_bucket.bucket,
            database=postgres_database.database if postgres_database else None,
            vpc=pacd_vpc.vpc,
        )
        Tags.of(csv_mover).add(TAG_KEYS.MODULE, MODULES.COMPUTE)

        # Loads Firehose event files into PostgreSQL when enabled.
        category_events_to_postgres = CategoryEventsToPostgres(
            self,
            "CategoryEventsToPostgres",
            bucket=category_events_stream.bucket,
            database=postgres_database.database if postgres_database else None,
            vpc=pacd_vpc.vpc,
        )
        Tags.of(category_events_to_postgres).add(TAG_KEYS.MODULE, MODULES.DATABASE)

        # Reads category click totals from PostgreSQL when enabled.
        category_clicks_analytics = CategoryClicksAnalytics(
            self,
            "CategoryClicksAnalytics",
            database=postgres_database.database if postgres_database else None,
            vpc=pacd_vpc.vpc,
        )
        Tags.of(category_clicks_analytics).add(TAG_KEYS.MODULE, MODULES.COMPUTE)

        if postgres_database:
            # Opens PostgreSQL only to Lambda security groups.
            postgres_database.allow_connections_from(csv_mover.security_group)
            postgres_database.allow_connections_from(category_events_to_postgres.security_group, "category")
            postgres_database.allow_connections_from(category_clicks_analytics.security_group, "analytics")

        CfnOutput(
            self,
            "CsvUploadFunctionUrl",
            # Prints the public upload URL after deployment.
            value=csv_upload_url.function_url.url,
            description="Public demo URL for uploading CSV files to S3 inbound/.",
        )

        CfnOutput(
            self,
            "CategoryEventFunctionUrl",
            # Prints the public category event URL after deployment.
            value=category_events_stream.function_url.url,
            description="Public demo URL for sending category click events to Firehose.",
        )

        CfnOutput(
            self,
            "CategoryAnalyticsFunctionUrl",
            # Prints the public analytics URL after deployment.
            value=category_clicks_analytics.function_url.url,
            description="Public demo URL for reading category click analytics.",
        )

        CfnOutput(
            self,
            "ExternalApiEnrichmentFunctionUrl",
            # Prints the public external API enrichment URL after deployment.
            value=external_api_enrichment.function_url.url,
            description="Public demo URL for loading external products and caching category results in S3.",
        )

        CfnOutput(
            self,
            "CryptoPricesFunctionUrl",
            # Prints the public crypto prices URL after deployment.
            value=crypto_prices.function_url.url,
            description="Public demo URL for reading Binance BTC, ETH, and DOGE prices.",
        )
