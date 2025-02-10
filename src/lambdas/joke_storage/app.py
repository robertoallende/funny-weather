import json
import os
from datetime import datetime, timezone
from typing import Dict, Any

import boto3
from aws_lambda_powertools import Logger, Tracer
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.exceptions import ClientError

logger = Logger()
tracer = Tracer()

@logger.inject_lambda_context
@tracer.capture_lambda_handler
def handler(event: Dict[str, Any], context: LambdaContext) -> Dict[str, Any]:
    """
    Lambda handler to store joke data in DynamoDB
    """
    try:
        # Initialize DynamoDB resource with optional endpoint URL for testing
        dynamodb_args = {'service_name': 'dynamodb'}
        if 'DYNAMODB_ENDPOINT_URL' in os.environ:
            dynamodb_args['endpoint_url'] = os.environ['DYNAMODB_ENDPOINT_URL']
        
        dynamodb = boto3.resource(**dynamodb_args)
        
        # Get the table name from environment variables
        table_name = os.environ['DYNAMODB_TABLE']
        table = dynamodb.Table(table_name)
        
        # Extract joke data from the event
        joke_data = json.loads(event['detail']['body'])
        timestamp = event['detail']['timestamp']
        location = event['detail']['location']
        
        try:
            response = table.update_item(
                Key={
                    'timestamp': timestamp,
                    'location': location
                },
                UpdateExpression="SET joke_data = :j, #s = :c",
                ExpressionAttributeNames={
                    '#s': 'status'
                },
                ExpressionAttributeValues={
                    ':j': {
                        'emoji': joke_data['emoji'],
                        'weather_status': joke_data['weather_status'],
                        'jokes': joke_data['jokes']
                    },
                    ':c': 'COMPLETE'
                },
                ReturnValues="ALL_NEW"
            )
            
            logger.info(f"Successfully updated item in DynamoDB: {response['Attributes']}")
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Successfully stored joke data',
                    'timestamp': timestamp,
                    'location': location
                })
            }
            
        except ClientError as e:
            logger.error(f"Error updating DynamoDB item: {str(e)}")
            return {
                'statusCode': 500,
                'body': json.dumps({
                    'error': 'Failed to update DynamoDB item',
                    'details': str(e)
                })
            }
            
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'details': str(e)
            })
        } 