import boto3
import json

client = boto3.client('bedrock-agent-runtime', region_name='us-east-1')

response = client.invoke_agent(
    agentId='VTWZZYOS6N',
    agentAliasId='TSTALIASID',
    sessionId='test-session-1',
    inputText='What is AWS Bedrock?'
)

completion = ""
for event in response['completion']:
    if 'chunk' in event:
        chunk = event['chunk']
        completion += chunk['bytes'].decode('utf-8')

print(completion)
