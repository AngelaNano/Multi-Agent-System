from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    RemovalPolicy,
    CfnOutput
)
from constructs import Construct

class MultiAgentStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # ── S3 BUCKET ──────────────────────────────────────────────
        # This is where all research documents live
        # Bedrock Knowledge Base will read from here
        self.documents_bucket = s3.Bucket(
            self,
            "DocumentsBucket",
            bucket_name=f"multi-agent-documents-{self.account}",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=True,
        )

        # ── IAM ROLE FOR BEDROCK ───────────────────────────────────
        # Gives Bedrock permission to read from S3
        # Without this role, Bedrock cannot touch your bucket
        self.bedrock_role = iam.Role(
            self,
            "BedrockRole",
            assumed_by=iam.ServicePrincipal("bedrock.amazonaws.com"),
            description="Allows Bedrock to read documents from S3",
        )

        # Grant Bedrock read access to the bucket
        self.documents_bucket.grant_read(self.bedrock_role)

        # ── OUTPUTS ───────────────────────────────────────────────
        # These print your bucket name and role ARN after deployment
        # You'll need these values in later phases
        CfnOutput(self, "BucketName",
            value=self.documents_bucket.bucket_name,
            description="S3 bucket for research documents"
        )

        CfnOutput(self, "BedrockRoleArn",
            value=self.bedrock_role.role_arn,
            description="IAM role ARN for Bedrock"
        )