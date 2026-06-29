#!/usr/bin/env python3
"""CDK application entry point for the Trading Application infrastructure.

The DevOps Agent webhook URL and HMAC shared secret are read from CDK context.
Workshop Module 0 sets them at deploy time:

    cdk deploy \\
      -c devops_agent_webhook_url=<webhook-url> \\
      -c devops_agent_webhook_secret=<shared-secret>

When either value is empty (the default), no webhook secret is created in
Secrets Manager and the Lambda short-circuits at invocation time. This keeps
local / sandbox deploys lightweight and the production-ready integration
narrowly scoped to participants who configure the agent.
"""
import aws_cdk as cdk
from trading_stack import TradingAppStack

app = cdk.App()

devops_agent_webhook_url = app.node.try_get_context("devops_agent_webhook_url") or ""
devops_agent_webhook_secret = app.node.try_get_context("devops_agent_webhook_secret") or ""

TradingAppStack(
    app,
    "TradingAppStack",
    devops_agent_webhook_url=devops_agent_webhook_url,
    devops_agent_webhook_secret=devops_agent_webhook_secret,
)

app.synth()
