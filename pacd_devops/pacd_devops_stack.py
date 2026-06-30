from aws_cdk import (
    # Duration,
    Stack, Tags,
    # aws_sqs as sqs,
)
from constructs import Construct

from pacd_devops.alarms.monthly_budget_alarm import MonthlyBudgetAlarm
from pacd_devops.constants import TAG_KEYS, MODULES


class PacdDevopsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        monthly_budget = MonthlyBudgetAlarm(self, "MonthlyBudgetAlarm")
        Tags.of(monthly_budget).add(TAG_KEYS.MODULE, MODULES.BILLING)
