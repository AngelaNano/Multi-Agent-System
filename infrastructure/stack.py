from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_iam as iam,
    aws_lambda as lambda_,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
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
        self.lambda_role = iam.Role(
            self,
            "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ]
        )

        self.lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["bedrock:*"],
            resources=["*"]
        ))

        self.lambda_role.add_to_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                "bedrock-agent-runtime:InvokeAgent",
                "bedrock-agent-runtime:Retrieve",
            ],
            resources=["*"]
        ))

        self.documents_bucket.grant_read_write(self.lambda_role)

        # ── RESEARCH TOOL LAMBDA ───────────────────────────────────
        self.research_lambda = lambda_.Function(
            self,
            "ResearchTool",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="research_tool.handler",
            code=lambda_.Code.from_asset("lambda"),
            role=self.lambda_role,
            timeout=Duration.seconds(60),
            environment={
                "KNOWLEDGE_BASE_ID": "LQXGE7QUHO"
            }
        )

        # ── ANALYSIS TOOL LAMBDA ───────────────────────────────────
        self.analysis_lambda = lambda_.Function(
            self,
            "AnalysisTool",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="analysis_tool.handler",
            code=lambda_.Code.from_asset("lambda"),
            role=self.lambda_role,
            timeout=Duration.seconds(60),
            environment={
                "BUCKET_NAME": self.documents_bucket.bucket_name
            }
        )

        # ── WRITER TOOL LAMBDA ─────────────────────────────────────
        self.writer_lambda = lambda_.Function(
            self,
            "WriterTool",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="writer_tool.handler",
            code=lambda_.Code.from_asset("lambda"),
            role=self.lambda_role,
            timeout=Duration.seconds(60),
            environment={
                "BUCKET_NAME": self.documents_bucket.bucket_name
            }
        )

        # ── ORCHESTRATOR LAMBDA ────────────────────────────────────
        self.orchestrator_lambda = lambda_.Function(
            self,
            "Orchestrator",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="orchestrator.handler",
            code=lambda_.Code.from_asset("lambda"),
            role=self.lambda_role,
            timeout=Duration.seconds(300),
            environment={
                "BUCKET_NAME": self.documents_bucket.bucket_name,
                "RESEARCH_AGENT_ID": "VTWZZYOS6N",
                "RESEARCH_AGENT_ALIAS": "TSTALIASID"
            }
        )

        # ── STEP FUNCTIONS STATE MACHINE ───────────────────────────
        # Define each step as a Lambda invocation task
        
        # Step 1: Research
        research_task = tasks.LambdaInvoke(
            self,
            "ResearchTask",
            lambda_function=self.orchestrator_lambda,
            output_path="$.Payload",
            comment="Invoke research agent to gather information"
        )

        # Step 2: Wait for human approval (HITL)
        # This pauses the workflow and waits for a human to approve
        wait_for_approval = sfn.Pass(
            self,
            "WaitForApproval",
            comment="Human in the loop checkpoint"
        )

        # Step 3: Complete
        complete = sfn.Succeed(
            self,
            "WorkflowComplete",
            comment="Research report generated successfully"
        )

        # Chain the steps together
        # Research → Approval → Complete
        definition = research_task.next(wait_for_approval).next(complete)

        # Create the state machine
        self.state_machine = sfn.StateMachine(
            self,
            "ResearchStateMachine",
            state_machine_name="multi-agent-research-pipeline",
            definition_body=sfn.DefinitionBody.from_chainable(definition),
            timeout=Duration.minutes(30),
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

        CfnOutput(self, "StateMachineArn",
            value=self.state_machine.state_machine_arn,
            description="ARN of the Step Functions state machine"
        )