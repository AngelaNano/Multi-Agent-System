from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import boto3
import json
import os
from datetime import datetime

app = FastAPI(
    title="Multi-Agent Research System",
    description="AI-powered research pipeline using AWS Bedrock Agents",
    version="1.0.0"
)

# Allow Streamlit to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# AWS clients
stepfunctions = boto3.client('stepfunctions', region_name='us-east-1')
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
s3_client = boto3.client('s3', region_name='us-east-1')

STATE_MACHINE_ARN = "arn:aws:states:us-east-1:160489847335:stateMachine:multi-agent-research-pipeline"
SESSIONS_TABLE = "multi-agent-sessions"
BUCKET_NAME = "multi-agent-documents-160489847335"

# ── REQUEST/RESPONSE MODELS ────────────────────────────────────────
class ResearchRequest(BaseModel):
    topic: str
    session_id: str = ""

class ResearchResponse(BaseModel):
    execution_arn: str
    session_id: str
    status: str
    message: str

# ── ROUTES ────────────────────────────────────────────────────────

@app.get("/")
def root():
    """Health check endpoint"""
    return {
        "status": "online",
        "service": "Multi-Agent Research System",
        "version": "1.0.0"
    }

@app.post("/research", response_model=ResearchResponse)
def start_research(request: ResearchRequest):
    """
    Start a new research pipeline execution.
    Triggers Step Functions which runs all 3 agents in sequence.
    """
    session_id = request.session_id or f"session-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    
    try:
        response = stepfunctions.start_execution(
            stateMachineArn=STATE_MACHINE_ARN,
            input=json.dumps({
                "topic": request.topic,
                "session_id": session_id
            })
        )
        
        return ResearchResponse(
            execution_arn=response['executionArn'],
            session_id=session_id,
            status="STARTED",
            message=f"Research pipeline started for topic: {request.topic}"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{execution_arn:path}")
def get_status(execution_arn: str):
    """
    Check the status of a pipeline execution.
    Returns current step and progress from DynamoDB checkpoints.
    """
    try:
        response = stepfunctions.describe_execution(
            executionArn=execution_arn
        )
        
        status = response['status']
        output = None
        
        if response.get('output'):
            output = json.loads(response['output'])
        
        return {
            "status": status,
            "output": output,
            "started_at": response['startDate'].isoformat(),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/session/{session_id}")
def get_session_checkpoints(session_id: str):
    """
    Get all DynamoDB checkpoints for a session.
    Shows exactly which steps completed and when.
    """
    try:
        table = dynamodb.Table(SESSIONS_TABLE)
        response = table.query(
            KeyConditionExpression=boto3.dynamodb.conditions.Key('session_id').eq(session_id)
        )
        return {
            "session_id": session_id,
            "checkpoints": response['Items']
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports")
def list_reports():
    """
    List all generated reports in S3.
    """
    try:
        response = s3_client.list_objects_v2(
            Bucket=BUCKET_NAME,
            Prefix="reports/"
        )
        
        reports = []
        for obj in response.get('Contents', []):
            reports.append({
                "key": obj['Key'],
                "size": obj['Size'],
                "last_modified": obj['LastModified'].isoformat()
            })
        
        return {"reports": reports, "total": len(reports)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/report/{report_key:path}")
def get_report(report_key: str):
    """
    Download a specific report from S3.
    """
    try:
        response = s3_client.get_object(
            Bucket=BUCKET_NAME,
            Key=report_key
        )
        content = response['Body'].read().decode('utf-8')
        return {"report_key": report_key, "content": content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))