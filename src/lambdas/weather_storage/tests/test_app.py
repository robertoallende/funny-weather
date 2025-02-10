import pytest
from datetime import datetime, timedelta
from decimal import Decimal
import json
import os
from unittest.mock import Mock, patch
import boto3
import moto

# Add path to import app
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from app import (
    convert_floats_to_decimals,
    calculate_ttl,
    store_weather_data,
    handler
)

@pytest.fixture
def sample_weather_data():
    """Fixture providing sample weather data"""
    return {
        'location': 'Wellington',
        'temperature': 288.15,  # 15°C
        'wind_speed': 25.0,
        'cloud_cover': 75,
        'visibility': 10000,
        'humidity': 85,
        'timestamp': '2025-02-11T10:00:00Z'
    }

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'ap-southeast-2'

@pytest.fixture
def dynamodb_table(aws_credentials):
    """Create a mock DynamoDB table using moto"""
    with moto.mock_dynamodb():
        dynamodb = boto3.resource('dynamodb', region_name='ap-southeast-2')
        
        # Create the DynamoDB table
        table = dynamodb.create_table(
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
        
        yield table

@pytest.fixture
def mock_events_client():
    """Fixture providing a mock EventBridge client"""
    with patch('boto3.client') as mock_client:
        mock_events = Mock()
        mock_client.return_value = mock_events
        yield mock_events

def test_convert_floats_to_decimals():
    """Test conversion of float values to Decimal"""
    test_data = {
        'float_value': 1.23,
        'int_value': 456,
        'string_value': 'test',
        'nested': {
            'float_value': 7.89,
            'int_value': 100
        }
    }
    
    result = convert_floats_to_decimals(test_data)
    
    assert isinstance(result['float_value'], Decimal)
    assert isinstance(result['int_value'], Decimal)
    assert isinstance(result['string_value'], str)
    assert isinstance(result['nested']['float_value'], Decimal)
    assert isinstance(result['nested']['int_value'], Decimal)
    assert str(result['float_value']) == '1.23'
    assert str(result['int_value']) == '456'
    assert str(result['nested']['float_value']) == '7.89'
    assert str(result['nested']['int_value']) == '100'

def test_calculate_ttl():
    """Test TTL calculation"""
    now = datetime.now()
    ttl = calculate_ttl(days=30)
    expected_ttl = int((now + timedelta(days=30)).timestamp())
    
    # Allow for 1 second difference due to execution time
    assert abs(ttl - expected_ttl) <= 1

@patch('app.table')
def test_store_weather_data_success(mock_table, sample_weather_data):
    """Test successful weather data storage"""
    # Call the function
    result = store_weather_data(sample_weather_data)
    
    # Verify DynamoDB put_item was called
    mock_table.put_item.assert_called_once()
    
    # Verify the stored item structure
    assert result['timestamp'] == sample_weather_data['timestamp']
    assert result['location'] == 'Wellington'
    assert result['status'] == 'PENDING'
    assert isinstance(result['ttl'], int)
    
    # Verify weather data conversion
    weather_data = result['weather_data']
    assert isinstance(weather_data['temperature'], Decimal)
    assert isinstance(weather_data['wind_speed'], Decimal)
    assert isinstance(weather_data['cloud_cover'], Decimal)
    assert isinstance(weather_data['visibility'], Decimal)
    assert isinstance(weather_data['humidity'], Decimal)
    assert isinstance(weather_data['precipitation'], Decimal)

@patch('app.table')
def test_store_weather_data_error(mock_table, sample_weather_data):
    """Test error handling in weather data storage"""
    # Make DynamoDB throw an error
    mock_table.put_item.side_effect = Exception("DynamoDB error")
    
    # Verify the error is propagated
    with pytest.raises(Exception) as exc_info:
        store_weather_data(sample_weather_data)
    assert str(exc_info.value) == "DynamoDB error"

@patch('app.table')
def test_handler_success(mock_table, sample_weather_data, mock_events_client):
    """Test successful Lambda handler execution"""
    # Create test event
    test_event = {'body': sample_weather_data}
    
    # Create mock context
    context = Mock()
    context.function_name = "weather-storage"
    
    # Call handler
    response = handler(test_event, context)
    
    # Verify response
    assert response['statusCode'] == 200
    response_body = json.loads(response['body'])
    assert response_body['message'] == 'Weather data stored successfully'
    assert response_body['data']['location'] == 'Wellington'
    
    # Verify EventBridge event was published
    mock_events_client.put_events.assert_called_once()
    event_entries = mock_events_client.put_events.call_args[1]['Entries']
    assert len(event_entries) == 1
    assert event_entries[0]['Source'] == 'custom.funnyweather'
    assert event_entries[0]['DetailType'] == 'WeatherFetched'

@patch('app.table')
def test_handler_invalid_input(mock_table, mock_events_client):
    """Test handler with invalid input"""
    # Create test event with missing required fields
    test_event = {'body': {'location': 'Wellington'}}  # Missing weather data
    
    # Create mock context
    context = Mock()
    context.function_name = "weather-storage"
    
    # Call handler
    response = handler(test_event, context)
    
    # Verify error response
    assert response['statusCode'] == 500
    response_body = json.loads(response['body'])
    assert 'error' in response_body
    assert 'Internal server error' in response_body['error'] 