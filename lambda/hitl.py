import json
import boto3
import os
from datetime import datetime

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

def handler(event, context):
    """
    HITL (Human in the Loop) checkpoint handler.
    
    What this does:
    1. Receives the research results from the orchestrator
    2. Saves the full session state to DynamoDB (checkpoint)
    3. Auto-approves for now (in production, would send email/notification)
    4. Returns approval status to Step Functions
    
    In a real enterprise system, step 3 would:
    - Send an email to a reviewer with the research summary
    - Return a task token to Step Functions
    - Step Functions would PAUSE and wait
    - When reviewer clicks approve/reject in a UI, it sends the token back
    - Step Functions RESUMES from the checkpoint
    """
    
    print(f"HITL checkpoint called with event keys: {list(event.keys())}")
    
    table_name = os.environ.get('SESSIONS_TABLE', 'multi-agent-sessions')
    table = dynamodb.Table(table_name)
    
    session_id = event.get('session_id', 'unknown')
    topic = event.get('topic', 'unknown')
    timestamp = datetime.now().isoformat()
    
    # ── CHECKPOINT: Save full state to DynamoDB ────────────────────
    # This is the critical piece — if the workflow is paused for human
    # review, all progress is saved here so nothing is lost
    checkpoint_data = {
        'session_id': session_id,
        'timestamp': timestamp,
        'topic': topic,
        'status': 'PENDING_APPROVAL',
        'research_summary': str(event.get('steps', {}).get('research', ''))[:500],
        'analysis_summary': str(event.get('steps', {}).get('analysis', ''))[:500],
        'report_location': event.get('report_location', 'not saved'),
        'full_state': json.dumps(event)[:4000]
    }
    
    table.put_item(Item=checkpoint_data)
    print(f"Checkpoint saved to DynamoDB: session_id={session_id}")
    
    # ── AUTO-APPROVE for development purposes ─────────────────────
    # In production this would pause and wait for human input
    # For the portfolio project we auto-approve to demonstrate the flow
    approval_status = "approved"
    
    # Update DynamoDB with approval decision
    table.update_item(
        Key={
            'session_id': session_id,
            'timestamp': timestamp
        },
        UpdateExpression="SET #s = :status, approved_at = :approved_at",
        ExpressionAttributeNames={'#s': 'status'},
        ExpressionAttributeValues={
            ':status': 'APPROVED',
            ':approved_at': datetime.now().isoformat()
        }
    )
    
    print(f"Session {session_id} approved — continuing workflow")
    
    return {
        'session_id': session_id,
        'topic': topic,
        'approval_status': approval_status,
        'checkpoint_timestamp': timestamp,
        'report_location': event.get('report_location', 'not saved'),
        'message': f"Research on '{topic}' approved. Report saved to S3."
    }