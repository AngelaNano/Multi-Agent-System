import json
import boto3
import os

# Initialize the Bedrock client
# boto3 is the Python SDK that talks to AWS services
bedrock_agent_runtime = boto3.client(
    service_name='bedrock-agent-runtime',
    region_name='us-east-1'
)

def handler(event, context):
    """
    This is the Lambda handler function.
    Every Lambda function needs a handler — it's the entry point.
    AWS calls this function when the agent needs to use this tool.
    
    event: contains the input from the Bedrock Agent
    context: contains metadata about the Lambda execution
    """
    
    print(f"Research tool called with event: {json.dumps(event)}")
    
    # Extract the query from the agent's request
    # The agent sends parameters when it calls this tool
    properties = event.get('requestBody', {}).get('content', {}).get('application/json', {}).get('properties', [])
    
    query = None
    for prop in properties:
        if prop.get('name') == 'query':
            query = prop.get('value')
            break
    
    if not query:
        return {
            'statusCode': 400,
            'body': json.dumps({'error': 'No query provided'})
        }
    
    # Get the Knowledge Base ID from environment variables
    # We set this when we deploy the Lambda
    knowledge_base_id = os.environ.get('KNOWLEDGE_BASE_ID')
    
    # Query the Bedrock Knowledge Base
    # This is the same retrieval we tested from the terminal
    response = bedrock_agent_runtime.retrieve(
        knowledgeBaseId=knowledge_base_id,
        retrievalQuery={
            'text': query
        },
        retrievalConfiguration={
            'vectorSearchConfiguration': {
                'numberOfResults': 3  # Return top 3 most relevant chunks
            }
        }
    )
    
    # Extract the text from the retrieval results
    results = []
    for result in response.get('retrievalResults', []):
        results.append({
            'text': result['content']['text'],
            'source': result['location']['s3Location']['uri']
        })
    
    # Format the response back to the agent
    # The agent reads this and uses it to formulate its answer
    return {
        'statusCode': 200,
        'body': json.dumps({
            'query': query,
            'results': results,
            'total_results': len(results)
        })
    }