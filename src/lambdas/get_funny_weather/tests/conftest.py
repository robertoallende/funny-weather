import pytest
import boto3
import os
from datetime import datetime, timezone
from moto import mock_dynamodb

@pytest.fixture(autouse=True)
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'ap-southeast-2'
    os.environ['LOCAL_DEVELOPMENT'] = 'true'  # Disable X-Ray for testing
    os.environ['DYNAMODB_TABLE'] = 'funny-weather-entries'
    # Clear any existing endpoint URL
    if 'AWS_ENDPOINT_URL' in os.environ:
        del os.environ['AWS_ENDPOINT_URL']

@pytest.fixture(scope='function')
def mock_dynamodb_service():
    """Create mock DynamoDB service."""
    with mock_dynamodb():
        yield

@pytest.fixture(scope='function')
def dynamodb(mock_dynamodb_service):
    """Get DynamoDB client."""
    return boto3.client('dynamodb', region_name='ap-southeast-2')

@pytest.fixture(scope='function')
def weather_table(dynamodb):
    """Create a mock weather table with test data."""
    # Create table
    dynamodb.create_table(
        TableName='funny-weather-entries',
        KeySchema=[
            {'AttributeName': 'location', 'KeyType': 'HASH'},
            {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
        ],
        AttributeDefinitions=[
            {'AttributeName': 'location', 'AttributeType': 'S'},
            {'AttributeName': 'timestamp', 'AttributeType': 'S'}
        ],
        BillingMode='PAY_PER_REQUEST'
    )

    # Insert test data
    dynamodb.put_item(
        TableName='funny-weather-entries',
        Item={
            'timestamp': {'S': datetime.now(timezone.utc).isoformat()},
            'location': {'S': 'Wellington'},
            'weather_data': {'M': {
                'temperature': {'N': '288.15'},  # 15°C
                'wind_speed': {'N': '25.0'},
                'cloud_cover': {'N': '75'},
                'visibility': {'N': '10000'},
                'humidity': {'N': '85'}
            }},
            'joke_data': {'M': {
                'emoji': {'S': '🌧️'},
                'weather_status': {'S': 'Windy with light rain'},
                'jokes': {'L': [
                    {'S': 'Why did the weather report go to therapy? It was dealing with too many cloudy issues!'}
                ]}
            }},
            'status': {'S': 'COMPLETE'}
        }
    )

    return dynamodb 