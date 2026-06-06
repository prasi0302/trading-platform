#!/usr/bin/env python3
"""CDK application entry point for the Trading Application infrastructure."""

import aws_cdk as cdk

from trading_stack import TradingAppStack

app = cdk.App()

TradingAppStack(
    app,
    "TradingAppStack",
    env=cdk.Environment(account="288282347955", region="us-east-1"),
)

app.synth()
