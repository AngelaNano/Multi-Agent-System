from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_opensearchserverless as oss,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct

class MultiAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ── S3 BUCKET ──────────────────────────────────────────────
        self.documents_bucket = s3.Bucket(
            self,
            "DocumentsBucket",
            bucket_name=f"multi-agent-documents-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=True,
        )

        # ── IAM ROLE FOR BEDROCK ───────────────────────────────────
        self.bedrock_role = iam.Role(
            self,
            "BedrockRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Allows Bedrock to read documents from S3",
        )

        # Grant Bedrock read access to the bucket
        self.documents_bucket.grant_read(self.bedrock_role)

        # Grant Bedrock full access to OpenSearch Serverless
        self.bedrock_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "aoss:APIAccessAll",
                "aoss:List*",
                "aoss:Get*",
                "aoss:Create*",
                "aoss:Update*",
                "aoss:Delete*",
                "aoss:BatchGet*",
            ],
            resources=["*"]
        ))

        # Grant Bedrock Knowledge Base permissions
        self.bedrock_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:*",
            ],
            resources=["*"]
        ))

        # ── OUTPUTS ───────────────────────────────────────────────
        CfnOutput(self, "BucketName",
            value=self.documents_bucket.bucket_name,
            description="S3 bucket for research documents"
        )

        CfnOutput(self, "BedrockRoleArn",
            value=self.bedrock_role.role_arn,
            description="IAM role ARN for Bedrock"
        )