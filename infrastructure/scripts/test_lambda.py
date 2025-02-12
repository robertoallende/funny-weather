import boto3
import json

# Initialize Lambda client
lambda_client = boto3.client('lambda',
    endpoint_url='http://localhost:4566',
    region_name='ap-southeast-2',
    aws_access_key_id='test',
    aws_secret_access_key='test'
)

try:
    # Invoke Lambda function
    print("Invoking Lambda function...")
    response = lambda_client.invoke(
        FunctionName='get-funny-weather',
        InvocationType='RequestResponse',
        LogType='Tail'
    )
    
    # Get the logs
    import base64
    logs = base64.b64decode(response['LogResult']).decode('utf-8')
    print("\nLambda Logs:")
    print(logs)
    
    # Get the response
    payload = json.loads(response['Payload'].read().decode('utf-8'))
    print("\nLambda Response:")
    print(json.dumps(payload, indent=2))
    
except Exception as e:
    print(f"Error: {str(e)}") 