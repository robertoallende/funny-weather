import os
import sys
from pathlib import Path

# Add the parent directory to PYTHONPATH
sys.path.append(str(Path(__file__).parent.parent))

from unittest.mock import patch, MagicMock
import pytest
import json
from botocore.exceptions import ClientError

# Import the handler function
from app import handler

# Mock AWS Lambda context
class MockContext:
    def __init__(self):
        self.function_name = "joke-storage"
        self.memory_limit_in_mb = 128
        self.invoked_function_arn = "arn:aws:lambda:local:123456789012:function:joke-storage"
        self.aws_request_id = "local-123"

# Test event fixture
@pytest.fixture
def valid_event():
    return {
        "detail": {
            "timestamp": "2025-02-11T10:00:00Z",
            "location": "Wellington",
            "body": json.dumps({
                "emoji": "🌧️",
                "weather_status": "Windy with light rain",
                "jokes": [
                    "Why did the weather report go to therapy? It was dealing with too many cloudy issues!",
                    "What's a cloud's favorite TV show? Precipitation Nation!"
                ]
            })
        }
    }

@pytest.fixture
def mock_dynamodb():
    with patch('boto3.resource') as mock_resource:
        # Create mock table
        mock_table = MagicMock()
        # Configure resource to return our mock table
        mock_resource.return_value.Table.return_value = mock_table
        yield mock_table

def test_successful_joke_storage(valid_event, mock_dynamodb):
    """Test successful joke storage operation"""
    # Configure mock response
    mock_dynamodb.update_item.return_value = {
        'Attributes': {
            'timestamp': '2025-02-11T10:00:00Z',
            'location': 'Wellington',
            'joke_data': {
                'emoji': '🌧️',
                'weather_status': 'Windy with light rain',
                'jokes': ['Test joke 1', 'Test joke 2']
            },
            'status': 'COMPLETE'
        }
    }

    # Set required environment variable
    os.environ['DYNAMODB_TABLE'] = 'test-table'

    # Call handler
    response = handler(valid_event, MockContext())

    # Verify response
    assert response['statusCode'] == 200
    body = json.loads(response['body'])
    assert body['message'] == 'Successfully stored joke data'
    assert body['timestamp'] == '2025-02-11T10:00:00Z'
    assert body['location'] == 'Wellington'

    # Verify DynamoDB update was called correctly
    mock_dynamodb.update_item.assert_called_once()
    call_kwargs = mock_dynamodb.update_item.call_args.kwargs
    assert call_kwargs['Key']['timestamp'] == '2025-02-11T10:00:00Z'
    assert call_kwargs['Key']['location'] == 'Wellington'

def test_dynamodb_error(valid_event, mock_dynamodb):
    """Test handling of DynamoDB errors"""
    # Configure mock to raise an error
    mock_dynamodb.update_item.side_effect = ClientError(
        {
            'Error': {
                'Code': 'ConditionalCheckFailedException',
                'Message': 'The conditional request failed'
            }
        },
        'UpdateItem'
    )

    # Set required environment variable
    os.environ['DYNAMODB_TABLE'] = 'test-table'

    # Call handler and verify error response
    response = handler(valid_event, MockContext())
    
    # Verify error response
    assert response['statusCode'] == 500
    body = json.loads(response['body'])
    assert 'error' in body
    assert 'ConditionalCheckFailedException' in body['details']

def test_missing_table_name():
    """Test handling of missing table name"""
    # Remove the environment variable
    if 'DYNAMODB_TABLE' in os.environ:
        del os.environ['DYNAMODB_TABLE']

    response = handler({}, MockContext())
    assert response['statusCode'] == 500
    assert 'error' in json.loads(response['body'])

def test_invalid_event_format(mock_dynamodb):
    """Test handling of invalid event format"""
    invalid_event = {
        "detail": {
            "timestamp": "2025-02-11T10:00:00Z",
            # Missing location
            "body": json.dumps({
                "emoji": "🌧️"
                # Missing required fields
            })
        }
    }

    response = handler(invalid_event, MockContext())
    assert response['statusCode'] == 500
    assert 'error' in json.loads(response['body'])

def test_invalid_json_in_body(mock_dynamodb):
    """Test handling of invalid JSON in body"""
    invalid_event = {
        "detail": {
            "timestamp": "2025-02-11T10:00:00Z",
            "location": "Wellington",
            "body": "invalid json"
        }
    }

    response = handler(invalid_event, MockContext())
    assert response['statusCode'] == 500
    assert 'error' in json.loads(response['body']) 