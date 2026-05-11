import json
import boto3
import os
from datetime import datetime

bedrock_runtime = boto3.client('bedrock-runtime', region_name='us-east-1')
bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name='us-east-1')
s3_client = boto3.client('s3', region_name='us-east-1')

def handler(event, context):
    print(f"Orchestrator called with event: {json.dumps(event)}")
    
    topic = event.get('topic', 'artificial intelligence')
    session_id = event.get('session_id', 'default-session')
    knowledge_base_id = os.environ.get('KNOWLEDGE_BASE_ID', 'LQXGE7QUHO')
    bucket_name = os.environ.get('BUCKET_NAME')

    results = {
        'topic': topic,
        'session_id': session_id,
        'steps': {}
    }

    # ── STEP 1: RESEARCH ──────────────────────────────────────────
    print(f"Step 1: Researching topic: {topic}")
    kb_response = bedrock_agent_runtime.retrieve(
        knowledgeBaseId=knowledge_base_id,
        retrievalQuery={'text': topic},
        retrievalConfiguration={
            'vectorSearchConfiguration': {'numberOfResults': 3}
        }
    )
    
    research_chunks = []
    for result in kb_response.get('retrievalResults', []):
        research_chunks.append(result['content']['text'])
    
    research_result = '\n\n'.join(research_chunks)
    results['steps']['research'] = research_result
    print(f"Research complete: {research_result[:100]}...")

    # ── STEP 2: ANALYSIS ──────────────────────────────────────────
    print(f"Step 2: Analyzing research results")
    analysis_response = bedrock_runtime.invoke_model(
        modelId='us.anthropic.claude-haiku-4-5-20251001-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [{
                "role": "user",
                "content": f"Analyze these research findings about '{topic}' and provide key findings, patterns, and insights:\n\n{research_result}"
            }]
        })
    )
    analysis_body = json.loads(analysis_response['body'].read())
    analysis_result = analysis_body['content'][0]['text']
    results['steps']['analysis'] = analysis_result
    print(f"Analysis complete: {analysis_result[:100]}...")

    # ── STEP 3: WRITE REPORT ──────────────────────────────────────
    print(f"Step 3: Writing final report")
    report_response = bedrock_runtime.invoke_model(
        modelId='us.anthropic.claude-haiku-4-5-20251001-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [{
                "role": "user",
                "content": f"Write a comprehensive research report about '{topic}' based on:\n\nResearch: {research_result}\n\nAnalysis: {analysis_result}\n\nInclude: Executive Summary, Key Findings, Analysis, Conclusions."
            }]
        })
    )
    report_body = json.loads(report_response['body'].read())
    report_result = report_body['content'][0]['text']
    results['steps']['report'] = report_result

    # ── SAVE REPORT TO S3 ─────────────────────────────────────────
    if bucket_name:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_key = f"reports/{topic.replace(' ', '_')}_{timestamp}.txt"
        
        full_report = f"""RESEARCH REPORT: {topic}
{'='*50}

RESEARCH FINDINGS:
{research_result}

ANALYSIS:
{analysis_result}

FINAL REPORT:
{report_result}
"""
        s3_client.put_object(
            Bucket=bucket_name,
            Key=report_key,
            Body=full_report.encode('utf-8')
        )
        results['report_location'] = f"s3://{bucket_name}/{report_key}"
        print(f"Report saved to {results['report_location']}")

    results['status'] = 'completed'
    return results