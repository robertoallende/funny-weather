import os
import json
import boto3
from datetime import datetime, timezone
from aws_lambda_powertools import Logger
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

logger = Logger()

def get_dynamodb_client():
    """Get DynamoDB client"""
    endpoint_url = os.environ.get('AWS_ENDPOINT_URL')
    
    client_kwargs = {
        'region_name': os.environ.get('AWS_DEFAULT_REGION', 'ap-southeast-2')
    }
    
    # For LocalStack testing
    if endpoint_url:
        if 'LOCALSTACK_HOSTNAME' in os.environ:
            endpoint_url = f"http://{os.environ['LOCALSTACK_HOSTNAME']}:4566"
        
        client_kwargs.update({
            'endpoint_url': endpoint_url,
            'aws_access_key_id': 'test',
            'aws_secret_access_key': 'test',
            'verify': False
        })
    
    return boto3.client('dynamodb', **client_kwargs)

@logger.inject_lambda_context
def handler(event: dict, context: LambdaContext) -> dict:
    """
    Handler for getFunnyWeather API endpoint
    """
    # Add CORS headers
    headers = {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token',
        'Access-Control-Allow-Methods': 'GET,OPTIONS'
    }

    # Handle OPTIONS request
    if event.get('httpMethod') == 'OPTIONS':
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps({'message': 'CORS preflight handled'})
        }

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
            ScanIndexForward=False
        )
        
        # Check if we got any results
        if not response['Items']:
            return {
                'statusCode': 404,
                'headers': headers,
                'body': json.dumps({
                    'error': 'No weather data found for Wellington'
                })
            }
        
        # Format the response
        item = response['Items'][0]
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
            
        return {
            'statusCode': 200,
            'headers': headers,
            'body': json.dumps(formatted_response)
        }
        
    except ClientError as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Failed to fetch weather data'
            })
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': headers,
            'body': json.dumps({
                'error': 'Internal server error'
            })
        } 