import os
import pytest
from unittest.mock import patch

def pytest_configure(config):
    """Configure test environment"""
    os.environ['AWS_ACCESS_KEY_ID'] = 'testing'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'testing'
    os.environ['AWS_SECURITY_TOKEN'] = 'testing'
    os.environ['AWS_SESSION_TOKEN'] = 'testing'
    os.environ['AWS_DEFAULT_REGION'] = 'ap-southeast-2'
    os.environ['DYNAMODB_TABLE'] = 'funny_weather_entries'

@pytest.fixture(autouse=True)
def mock_boto3_client():
    """Mock boto3 client to avoid actual AWS calls"""
    with patch('boto3.client'), patch('boto3.resource'):
        yield 