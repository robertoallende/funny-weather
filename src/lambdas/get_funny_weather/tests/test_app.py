import pytest
import json
import os
from src.lambdas.get_funny_weather.app import handler, get_dynamodb_client

def test_get_weather_success(weather_table):
    """Test successful weather data retrieval."""
    # Mock Lambda context
    class MockContext:
        def __init__(self):
            self.function_name = "get-funny-weather"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = "arn:aws:lambda:local:123456789012:function:get-funny-weather"
            self.aws_request_id = "test-123"
    
    # Call handler
    response = handler({}, MockContext())
    
    # Assert response structure
    assert response['statusCode'] == 200
    
    body = json.loads(response['body'])
    assert 'location' in body
    assert 'timestamp' in body
    assert 'weather' in body
    assert 'joke' in body
    
    # Assert weather data
    weather = body['weather']
    assert weather['temperature_celsius'] == 15.0  # 288.15K - 273.15
    assert weather['wind_speed'] == 25.0
    assert weather['cloud_cover'] == 75.0
    assert weather['visibility'] == 10000.0
    assert weather['humidity'] == 85.0
    
    # Assert joke data
    joke = body['joke']
    assert joke['emoji'] == '🌧️'
    assert joke['weather_status'] == 'Windy with light rain'
    assert isinstance(joke['jokes'], list)
    assert len(joke['jokes']) == 1

def test_get_weather_no_data(weather_table):
    """Test when no weather data is available."""
    # Clear the table
    weather_table.delete_item(
        TableName='funny-weather-entries',
        Key={
            'location': {'S': 'Wellington'},
            'timestamp': {'S': weather_table.scan(TableName='funny-weather-entries')['Items'][0]['timestamp']['S']}
        }
    )
    
    # Mock Lambda context
    class MockContext:
        def __init__(self):
            self.function_name = "get-funny-weather"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = "arn:aws:lambda:local:123456789012:function:get-funny-weather"
            self.aws_request_id = "test-123"
    
    # Call handler
    response = handler({}, MockContext())
    
    # Assert response
    assert response['statusCode'] == 404
    body = json.loads(response['body'])
    assert 'error' in body
    assert body['error'] == 'No weather data found for Wellington'

def test_get_weather_missing_table(mock_dynamodb_service):
    """Test when DynamoDB table doesn't exist."""
    # Mock Lambda context
    class MockContext:
        def __init__(self):
            self.function_name = "get-funny-weather"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = "arn:aws:lambda:local:123456789012:function:get-funny-weather"
            self.aws_request_id = "test-123"
    
    # Call handler without creating table
    response = handler({}, MockContext())
    
    # Assert response
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body
    assert body['error'] == 'Failed to fetch weather data'

def test_get_weather_missing_env_var(weather_table):
    """Test when environment variable is missing."""
    # Remove required environment variable
    del os.environ['DYNAMODB_TABLE']
    
    # Mock Lambda context
    class MockContext:
        def __init__(self):
            self.function_name = "get-funny-weather"
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = "arn:aws:lambda:local:123456789012:function:get-funny-weather"
            self.aws_request_id = "test-123"
    
    # Call handler
    response = handler({}, MockContext())
    
    # Assert response
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body
    assert body['error'] == 'Internal server error'
    
    # Restore environment variable
    os.environ['DYNAMODB_TABLE'] = 'funny-weather-entries'

def test_dynamodb_client_configuration():
    """Test DynamoDB client configuration."""
    # Test with endpoint URL
    os.environ['AWS_ENDPOINT_URL'] = 'http://localhost:4566'
    client = get_dynamodb_client()
    assert client.meta.endpoint_url == 'http://localhost:4566'
    
    # Test with LocalStack hostname
    os.environ['LOCALSTACK_HOSTNAME'] = '172.18.0.2'
    client = get_dynamodb_client()
    assert client.meta.endpoint_url == 'http://172.18.0.2:4566'
    
    # Test without endpoint URL
    del os.environ['AWS_ENDPOINT_URL']
    del os.environ['LOCALSTACK_HOSTNAME']
    client = get_dynamodb_client()
    assert 'localhost' not in client.meta.endpoint_url 