import json
import boto3

bedrock_runtime = boto3.client(
    service_name='bedrock-runtime',
    region_name='us-east-1'
)

def handler(event, context):
    print(f"Analysis tool called with event: {json.dumps(event)}")
    
    # Extract research results from the agent's request
    properties = event.get('requestBody', {}).get('content', {}).get('application/json', {}).get('properties', [])
    
    research_data = None
    topic = None
    for prop in properties:
        if prop.get('name') == 'research_data':
            research_data = prop.get('value')
        if prop.get('name') == 'topic':
            topic = prop.get('value')
    
    if not research_data:
        research_data = event.get('inputText', '')
    
    # Use Claude to analyze the research data
    prompt = f"""Analyze the following research data about "{topic}" and provide:
1. Key findings and main points
2. Patterns and themes identified
3. Important relationships between concepts
4. Gaps or areas needing more research

Research data:
{research_data}

Provide a structured analysis."""

    response = bedrock_runtime.invoke_model(
        modelId='us.anthropic.claude-haiku-4-5-20251001-v1:0',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        })
    )
    
    response_body = json.loads(response['body'].read())
    analysis = response_body['content'][0]['text']
    
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
                        'analysis': analysis
                    })
                }
            }
        }
    }