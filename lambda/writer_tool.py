import json
import boto3
import os
from datetime import datetime

bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

s3_client = boto3.client('s3', region_name='us-east-1')

def handler(event, context):
    print(f"Writer tool called with event: {json.dumps(event)}")
    
    properties = event.get('requestBody', {}).get('content', {}).get('application/json', {}).get('properties', [])
    
    analysis = None
    topic = None
    for prop in properties:
        if prop.get('name') == 'analysis':
            analysis = prop.get('value')
        if prop.get('name') == 'topic':
            topic = prop.get('value')
    
    if not analysis:
        analysis = event.get('inputText', '')

    # Use Claude to write the final report
    prompt = f"""Based on the following analysis about "{topic}", write a comprehensive, 
well-structured research report. Include:

1. Executive Summary
2. Introduction
3. Key Findings
4. Detailed Analysis
5. Conclusions and Recommendations

Analysis to base the report on:
{analysis}

Write a professional, clear report."""

    response = bedrock_runtime.invoke_model(
        modelId='us.anthropic.claude-haiku-4-5-20251001-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 2000,
            "messages": [{"role": "user", "content": prompt}]
        })
    )
    
    response_body = json.loads(response['body'].read())
    report = response_body['content'][0]['text']
    
    # Save report to S3
    bucket_name = os.environ.get('BUCKET_NAME')
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_key = f"reports/{topic}_{timestamp}.txt"
    
    if bucket_name:
        s3_client.put_object(
            Bucket=bucket_name,
            Key=report_key,
            Body=report.encode('utf-8')
        )
        print(f"Report saved to s3://{bucket_name}/{report_key}")
    
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': event.get('actionGroup'),
            'apiPath': event.get('apiPath'),
            'httpMethod': event.get('httpMethod'),
            'httpStatusCode': 200,
            'responseBody': {
                'application/json': {
                    'body': json.dumps({
                        'topic': topic,
                        'report': report,
                        'saved_to': f"s3://{bucket_name}/{report_key}" if bucket_name else "not saved"
                    })
                }
            }
        }
    }