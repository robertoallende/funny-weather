import sys
from pathlib import Path
import os
import json
import boto3
from datetime import datetime
from decimal import Decimal

# Add the parent directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

# Set LocalStack environment variables before importing the handler
os.environ['LOCALSTACK_HOSTNAME'] = 'localhost'
os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
os.environ['AWS_DEFAULT_REGION'] = 'ap-southeast-2'
os.environ['DYNAMODB_TABLE'] = 'funny_weather_entries'

from app import handler

class DecimalEncoder(json.JSONEncoder):
    """Handle Decimal serialization for JSON encoding"""
    def default(self, obj):
        if isinstance(obj, Decimal):
            return str(obj)
        return super(DecimalEncoder, self).default(obj)

def setup_dynamodb_table():
    """Create DynamoDB table in LocalStack"""
    dynamodb = boto3.client('dynamodb', 
                          endpoint_url='http://localhost:4566',
                          region_name='ap-southeast-2',
                          aws_access_key_id='test',
                          aws_secret_access_key='test')
    
    try:
        dynamodb.create_table(
            TableName='funny_weather_entries',
            KeySchema=[
                {'AttributeName': 'timestamp', 'KeyType': 'HASH'},
                {'AttributeName': 'location', 'KeyType': 'RANGE'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'timestamp', 'AttributeType': 'S'},
                {'AttributeName': 'location', 'AttributeType': 'S'}
            ],
            BillingMode='PAY_PER_REQUEST'
        )
        print("DynamoDB table created successfully")
    except dynamodb.exceptions.ResourceInUseException:
        print("Table already exists")

def test_storage_lambda():
    """Test the weather storage lambda with sample data"""
    # Create test event
    test_event = {
        'body': {
            'location': 'Wellington',
            'temperature': 288.15,  # 15°C
            'wind_speed': 25.0,
            'cloud_cover': 75,
            'visibility': 10000,
            'humidity': 85,
            'timestamp': datetime.now().isoformat()
        }
    }
    
    # Mock Lambda context
    class MockContext:
        def __init__(self):
            self.function_name = "weather-storage"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = "arn:aws:lambda:local:123456789012:function:weather-storage"
            self.aws_request_id = "local-123"
    
    print("\nTesting weather storage with sample data...")
    print(f"Input event: {json.dumps(test_event, indent=2)}")
    
    # Call the handler
    response = handler(test_event, MockContext())
    
    print("\nLambda Response:")
    print(json.dumps({
        "statusCode": response["statusCode"],
        "body": json.loads(response["body"])
    }, indent=2))
    
    # Verify data in DynamoDB
    dynamodb = boto3.resource('dynamodb',
                            endpoint_url='http://localhost:4566',
                            region_name='ap-southeast-2',
                            aws_access_key_id='test',
                            aws_secret_access_key='test')
    
    table = dynamodb.Table('funny_weather_entries')
    stored_item = table.get_item(
        Key={
            'timestamp': test_event['body']['timestamp'],
            'location': test_event['body']['location']
        }
    ).get('Item')
    
    print("\nStored DynamoDB Item:")
    print(json.dumps(stored_item, indent=2, cls=DecimalEncoder))

if __name__ == "__main__":
    # Ensure LocalStack is running and table exists
    setup_dynamodb_table()
    test_storage_lambda() 