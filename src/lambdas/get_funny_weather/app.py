import os
import json
import boto3
from datetime import datetime, timezone
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

logger = Logger()

# Only enable tracing if not in local development
if not os.environ.get('LOCAL_DEVELOPMENT'):
    from aws_lambda_powertools import Tracer
    tracer = Tracer()
else:
    # Mock tracer for local development
    class MockTracer:
        def capture_lambda_handler(self, handler):
            return handler
        
        def capture_method(self, method):
            return method
    
    tracer = MockTracer()

def get_dynamodb_client():
    """Get DynamoDB client"""
    endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
    print(f"Using endpoint URL: {endpoint_url}")
    
    client_kwargs = {
        'region_name': os.environ.get('AWS_DEFAULT_REGION', 'ap-southeast-2')
    }
    
    # For LocalStack testing
    if endpoint_url:
        # Try to use internal network address if available
        if 'LOCALSTACK_HOSTNAME' in os.environ:
            endpoint_url = f"http://{os.environ['LOCALSTACK_HOSTNAME']}:4566"
        
        client_kwargs.update({
            'endpoint_url': endpoint_url,
            'aws_access_key_id': 'test',
            'aws_secret_access_key': 'test',
            'verify': False  # Disable SSL verification for LocalStack
        })
    
    print(f"DynamoDB client kwargs: {client_kwargs}")
    return boto3.client('dynamodb', **client_kwargs)

def deserialize_dynamodb_item(item):
    """Convert DynamoDB item to regular Python dict"""
    def _deserialize(value):
        if isinstance(value, dict):
            if 'S' in value:
                return value['S']
            elif 'N' in value:
                return float(value['N'])
            elif 'M' in value:
                return {k: _deserialize(v) for k, v in value['M'].items()}
            elif 'L' in value:
                return [_deserialize(v) for v in value['L']]
        return value

    return {k: _deserialize(v) for k, v in item.items()}

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: dict, context: LambdaContext) -> dict:
    """
    Handler for getFunnyWeather API endpoint
    
    Note: Currently hardcoded for Wellington. Future enhancement needed to support multiple locations.
    """
    try:
        print(f"Environment variables: {dict(os.environ)}")  # Debug output
        
        # Get DynamoDB client
        dynamodb = get_dynamodb_client()
        
        # Query the latest entry for Wellington
        print("Querying DynamoDB...")  # Debug output
        response = dynamodb.query(
            TableName=os.environ['DYNAMODB_TABLE'],
            KeyConditionExpression='#loc = :loc',
            ExpressionAttributeNames={
                '#loc': 'location',
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':loc': {'S': 'Wellington'},
                ':status': {'S': 'COMPLETE'}
            },
            FilterExpression='#status = :status',
            Limit=1,
            ScanIndexForward=False  # Get newest first
        )
        print(f"DynamoDB response: {response}")  # Debug output
        
        # Check if we got any results
        if not response['Items']:
            print("No items found")  # Debug output
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'No weather data found for Wellington'
                })
            }
        
        # Deserialize and format the response
        item = response['Items'][0]
        print(f"Found item: {item}")  # Debug output
        
        formatted_response = {
            'location': item['location']['S'],
            'timestamp': item['timestamp']['S'],
            'weather': {
                'temperature_celsius': round(float(item['weather_data']['M']['temperature']['N']) - 273.15, 1),
                'wind_speed': float(item['weather_data']['M']['wind_speed']['N']),
                'cloud_cover': float(item['weather_data']['M']['cloud_cover']['N']),
                'visibility': float(item['weather_data']['M']['visibility']['N']),
                'humidity': float(item['weather_data']['M']['humidity']['N'])
            },
            'joke': {
                'emoji': item['joke_data']['M']['emoji']['S'],
                'weather_status': item['joke_data']['M']['weather_status']['S'],
                'jokes': [j['S'] for j in item['joke_data']['M']['jokes']['L']]
            }
        }
            
        # Return the formatted response
        return {
            'statusCode': 200,
            'body': json.dumps(formatted_response)
        }
        
    except ClientError as e:
        print(f"DynamoDB error: {str(e)}")  # Debug output
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to fetch weather data'
            })
        }
    except Exception as e:
        print(f"Unexpected error: {str(e)}")  # Debug output
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error'
            })
        } 