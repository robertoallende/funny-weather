import json
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from typing import Dict, Any

logger = Logger()
tracer = Tracer()

def get_dynamodb_client():
    """Get DynamoDB client based on environment"""
    if os.getenv('AWS_SAM_LOCAL') or os.getenv('LOCALSTACK_HOSTNAME'):
        return boto3.resource('dynamodb',
                            endpoint_url='http://localhost:4566',
                            region_name=os.getenv('AWS_DEFAULT_REGION', 'ap-southeast-2'),
                            aws_access_key_id='test',
                            aws_secret_access_key='test')
    return boto3.resource('dynamodb')

# Initialize DynamoDB client
dynamodb = get_dynamodb_client()
table = dynamodb.Table(os.environ.get('DYNAMODB_TABLE', 'funny_weather_entries'))

def calculate_ttl(days: int = 30) -> int:
    """Calculate TTL timestamp for DynamoDB entry"""
    return int((datetime.now() + timedelta(days=days)).timestamp())

def convert_to_decimal(value):
    """Convert a value to Decimal for DynamoDB"""
    if isinstance(value, (int, float)):
        return Decimal(str(value))
    return value

@tracer.capture_method
def store_weather_data(weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """Store weather data in DynamoDB"""
    try:
        logger.info("Storing weather data", extra={"weather_data": weather_data})
        
        # Extract data from the event and convert numbers to Decimal
        item = {
            'location': weather_data['location'],
            'timestamp': weather_data['timestamp'],
            'weather_data': {
                'temperature': convert_to_decimal(weather_data['temperature']),
                'wind_speed': convert_to_decimal(weather_data['wind_speed']),
                'cloud_cover': convert_to_decimal(weather_data['cloud_cover']),
                'visibility': convert_to_decimal(weather_data['visibility']),
                'precipitation': convert_to_decimal(weather_data['precipitation']),
                'humidity': convert_to_decimal(weather_data['humidity'])
            },
            'status': 'PENDING',
            'ttl': convert_to_decimal(calculate_ttl())
        }
        
        # Store in DynamoDB
        table.put_item(Item=item)
        logger.info("Successfully stored weather data")
        return item
        
    except Exception as e:
        logger.error(f"Error storing weather data: {str(e)}")
        raise

class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal serialization for JSON encoding"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Lambda handler for weather storage"""
    try:
        logger.info("Processing event", extra={"event": event})
        
        # Extract weather data from the event
        if 'detail' in event:
            weather_data = event['detail']
        else:
            weather_data = json.loads(event.get('body', '{}'))
        
        # Store weather data
        stored_item = store_weather_data(weather_data)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Weather data stored successfully',
                'data': stored_item
            }, cls=DecimalEncoder)  # Use custom encoder for Decimal values
        }
        
    except Exception as e:
        logger.error(f"Error in handler: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        } 