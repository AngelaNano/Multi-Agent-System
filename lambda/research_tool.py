import json
import boto3
import os

bedrock_agent_runtime = boto3.client(
    service_name='bedrock-agent-runtime',
    region_name='us-east-1'
)

def handler(event, context):
    print(f"Research tool called with event: {json.dumps(event)}")
    
    # Extract query from the agent's request
    properties = event.get('requestBody', {}).get('content', {}).get('application/json', {}).get('properties', [])
    
    query = None
    for prop in properties:
        if prop.get('name') == 'query':
            query = prop.get('value')
            break
    
    if not query:
        # Try getting from inputText directly
        query = event.get('inputText', 'general research')
    
    print(f"Query extracted: {query}")
    
    knowledge_base_id = os.environ.get('KNOWLEDGE_BASE_ID')
    
    try:
        response = bedrock_agent_runtime.retrieve(
            knowledgeBaseId=knowledge_base_id,
            retrievalQuery={
                'text': query
            },
            retrievalConfiguration={
                'vectorSearchConfiguration': {
                    'numberOfResults': 3
                }
            }
        )
        
        results = []
        for result in response.get('retrievalResults', []):
            results.append({
                'text': result['content']['text'],
                'source': result['location']['s3Location']['uri']
            })
        
        response_body = {
            'application/json': {
                'body': json.dumps({
                    'query': query,
                    'results': results,
                    'total_results': len(results)
                })
            }
        }
        
    except Exception as e:
        print(f"Error retrieving from knowledge base: {str(e)}")
        response_body = {
            'application/json': {
                'body': json.dumps({
                    'error': str(e),
                    'query': query
                })
            }
        }
    
    # This is the exact format Bedrock Agents expects
    return {
        'messageVersion': '1.0',
        'response': {
            'actionGroup': event.get('actionGroup'),
            'apiPath': event.get('apiPath'),
            'httpMethod': event.get('httpMethod'),
            'httpStatusCode': 200,
            'responseBody': response_body
        }
    }