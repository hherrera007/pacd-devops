import os

from aws_cdk import aws_budgets as budgets
from constructs import Construct

class MonthlyBudgetAlarm(Construct):
    def __init__(self, scope: Construct, construct_id: str) -> None:
        super().__init__(scope, construct_id)

        # Email that receives budget notifications.
        alert_email = os.getenv("BUDGET_ALERT_EMAIL")


        # Monthly budget that tracks actual AWS cost.
        # Cost: AWS budget monitoring and email notifications are free.
        self.monthly_budget = budgets.CfnBudget(
            self,
            "MonthlyTenDollarBudget",
            budget=budgets.CfnBudget.BudgetDataProperty(
                budget_name="pacd-monthly-10-usd-budget",
                budget_type="COST",
                time_unit="MONTHLY",
                budget_limit=budgets.CfnBudget.SpendProperty(
                    amount=10,
                    unit="USD",
                ),
            ),
            notifications_with_subscribers=[
                budgets.CfnBudget.NotificationWithSubscribersProperty(
                    # Alert when actual monthly cost passes 80% of $10.
                    notification=budgets.CfnBudget.NotificationProperty(
                        comparison_operator="GREATER_THAN",
                        notification_type="ACTUAL",
                        threshold=80,
                        threshold_type="PERCENTAGE",
                    ),
                    subscribers=[
                        budgets.CfnBudget.SubscriberProperty(
                            address=alert_email,
                            subscription_type="EMAIL",
                        )
                    ],
                )
            ],
        )
