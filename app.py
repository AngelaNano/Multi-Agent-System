import aws_cdk as cdk
from infrastructure.stack import MultiAgentStack

app = cdk.App()

MultiAgentStack(app, "MultiAgentStack",
    env=cdk.Environment(
        account=app.node.try_get_context("account"),
        region="us-east-1"
    )
)

app.synth()