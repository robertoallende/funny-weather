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
    endpoint_url = os.environ.get('AWS_ENDPOINT_URL')  # For LocalStack testing
    client_kwargs = {
        'region_name': os.environ.get('AWS_DEFAULT_REGION', 'ap-southeast-2')
    }
    if endpoint_url:
        client_kwargs['endpoint_url'] = endpoint_url
    
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
        # Get DynamoDB client
        dynamodb = get_dynamodb_client()
        
        # Query the latest entry for Wellington
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
        
        # Check if we got any results
        if not response['Items']:
            return {
                'statusCode': 404,
                'body': json.dumps({
                    'error': 'No weather data found for Wellington'
                })
            }
        
        # Deserialize and format the response
        item = deserialize_dynamodb_item(response['Items'][0])
        formatted_response = {
            'location': item['location'],
            'timestamp': item['timestamp'],
            'weather': {
                'temperature_celsius': round(item['weather_data']['temperature'] - 273.15, 1),  # Convert K to °C
                'wind_speed': item['weather_data']['wind_speed'],
                'cloud_cover': item['weather_data']['cloud_cover'],
                'visibility': item['weather_data']['visibility'],
                'humidity': item['weather_data']['humidity']
            },
            'joke': {
                'emoji': item['joke_data']['emoji'],
                'weather_status': item['joke_data']['weather_status'],
                'jokes': item['joke_data']['jokes']
            }
        }
            
        # Return the formatted response
        return {
            'statusCode': 200,
            'body': json.dumps(formatted_response)
        }
        
    except ClientError as e:
        logger.error(f"DynamoDB error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to fetch weather data'
            })
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error'
            })
        } 