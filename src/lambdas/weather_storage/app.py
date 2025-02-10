import json
import os
from datetime import datetime, timedelta
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

def convert_floats_to_decimals(data: Dict[str, Any]) -> Dict[str, Any]:
    """Convert float values to Decimal for DynamoDB compatibility"""
    converted = {}
    for key, value in data.items():
        if isinstance(value, (float, int)):
            converted[key] = Decimal(str(value))
        elif isinstance(value, dict):
            converted[key] = convert_floats_to_decimals(value)
        else:
            converted[key] = value
    return converted

@tracer.capture_method
def store_weather_data(weather_data: Dict[str, Any]) -> Dict[str, Any]:
    """Store weather data in DynamoDB"""
    try:
        # Convert float values to Decimal
        weather_data = convert_floats_to_decimals(weather_data)
        
        item = {
            'timestamp': weather_data['timestamp'],
            'location': weather_data['location'],
            'weather_data': {
                'coordinates': {
                    'latitude': Decimal('-41.276825'),  # Fixed for Wellington
                    'longitude': Decimal('174.777969')
                },
                'temperature': weather_data['temperature'],
                'wind_speed': weather_data['wind_speed'],
                'cloud_cover': weather_data['cloud_cover'],
                'visibility': weather_data['visibility'],
                'precipitation': weather_data.get('precipitation', Decimal('0')),
                'humidity': weather_data['humidity']
            },
            'status': 'PENDING',
            'ttl': calculate_ttl()
        }
        
        table.put_item(Item=item)
        return item
        
    except Exception as e:
        logger.error(f"Error storing weather data: {str(e)}")
        raise

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """Lambda handler for weather storage"""
    try:
        # Extract weather data from the event
        weather_data = json.loads(event['body']) if isinstance(event.get('body'), str) else event.get('body', {})
        
        # Store weather data
        stored_item = store_weather_data(weather_data)
        
        # Convert Decimal back to float for the event
        event_detail = {
            'timestamp': stored_item['timestamp'],
            'location': stored_item['location'],
            'temperature': float(stored_item['weather_data']['temperature']),
            'wind_speed': float(stored_item['weather_data']['wind_speed']),
            'cloud_cover': float(stored_item['weather_data']['cloud_cover']),
            'visibility': float(stored_item['weather_data']['visibility']),
            'humidity': float(stored_item['weather_data']['humidity'])
        }
        
        # Create EventBridge client with LocalStack configuration if needed
        events_client_args = {}
        if os.getenv('AWS_SAM_LOCAL') or os.getenv('LOCALSTACK_HOSTNAME'):
            events_client_args.update({
                'endpoint_url': 'http://localhost:4566',
                'region_name': os.getenv('AWS_DEFAULT_REGION', 'ap-southeast-2'),
                'aws_access_key_id': 'test',
                'aws_secret_access_key': 'test'
            })
        
        events = boto3.client('events', **events_client_args)
        
        # Put event to trigger joke generator
        events.put_events(
            Entries=[
                {
                    'Source': 'custom.funnyweather',
                    'DetailType': 'WeatherFetched',
                    'Detail': json.dumps(event_detail)
                }
            ]
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Weather data stored successfully',
                'data': stored_item
            }, default=str)  # Handle Decimal serialization
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