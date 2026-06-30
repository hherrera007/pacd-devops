#!/usr/bin/env python3
# Tells the operating system to run this file with the Python 3 interpreter.

# Imports the os module so the app can read environment variables.
import os
from pathlib import Path

# Imports the AWS CDK library and gives it the shorter name cdk.
import aws_cdk as cdk

from pacd_devops.constants import TAG_KEYS, TAG_VALUES
# Imports the PACD stack class defined in the local pacd_devops package.
from pacd_devops.pacd_devops_stack import PacdDevopsStack


def load_env_file() -> None:
    # Loads local environment variables for CDK synth.
    env_path = Path(".env")
    if not env_path.exists():
        return

    for line in env_path.read_text().splitlines():
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


load_env_file()

# Creates the CDK application that will contain one or more stacks.
app = cdk.App()

# Builds the AWS environment using the account and region from environment variables.
pacd_env = cdk.Environment(account=os.getenv('AWS_ACCOUNT'), region=os.getenv('AWS_REGION'))

# Adds the PACD stack to the CDK app and assigns it the logical stack name.
pacd_stack = PacdDevopsStack(app, "PacdDevopsStack",
                # Tells CDK which AWS account and region this stack targets.
                env=pacd_env
                )
cdk.Tags.of(pacd_stack).add(TAG_KEYS.PROJECT, TAG_VALUES.PROJECT)
cdk.Tags.of(pacd_stack).add(TAG_KEYS.ENVIRONMENT, TAG_VALUES.ENVIRONMENT)

# Synthesizes the CDK app into a CloudFormation template.
app.synth()
