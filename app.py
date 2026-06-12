#!/usr/bin/env python3
import os
import aws_cdk as cdk
from infrastructure.serverless_stack import ServerlessStack

app = cdk.App()

ServerlessStack(
    app,
    "ServerlessStack",
    env=cdk.Environment(
        account=os.environ.get("CDK_DEFAULT_ACCOUNT"),
        region=os.environ.get("CDK_DEFAULT_REGION", "us-east-1"),
    ),
)

app.synth()
