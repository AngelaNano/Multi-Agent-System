from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as lambda_,
    RemovalPolicy,
    CfnOutput,
    Duration
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

        self.documents_bucket.grant_read(self.bedrock_role)

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

        self.bedrock_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["bedrock:*"],
            resources=["*"]
        ))

        # ── IAM ROLE FOR LAMBDA ────────────────────────────────────
        # Lambda needs its own role to call Bedrock and CloudWatch
        self.lambda_role = iam.Role(
            self,
            "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                # Allows Lambda to write logs to CloudWatch
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        # Allow Lambda to call Bedrock Knowledge Base
        self.lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock:Retrieve",
                "bedrock:RetrieveAndGenerate",
            ],
            resources=["*"]
        ))

        # Allow Lambda to read from S3
        self.documents_bucket.grant_read(self.lambda_role)

        # ── RESEARCH TOOL LAMBDA ───────────────────────────────────
        # This is the tool the Research Agent calls
        # It queries the Knowledge Base and returns relevant documents
        self.research_lambda = lambda_.Function(
            self,
            "ResearchTool",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="research_tool.handler",
            code=lambda_.Code.from_asset("lambda"),
            role=self.lambda_role,
            timeout=Duration.seconds(30),
            environment={
                # We'll fill in the Knowledge Base ID after deployment
                "KNOWLEDGE_BASE_ID": "PLACEHOLDER"
            }
        )

        # ── OUTPUTS ───────────────────────────────────────────────
        CfnOutput(self, "BucketName",
            value=self.documents_bucket.bucket_name,
            description="S3 bucket for research documents"
        )

        CfnOutput(self, "BedrockRoleArn",
            value=self.bedrock_role.role_arn,
            description="IAM role ARN for Bedrock"
        )

        CfnOutput(self, "ResearchLambdaArn",
            value=self.research_lambda.function_arn,
            description="ARN of the Research Tool Lambda"
        )