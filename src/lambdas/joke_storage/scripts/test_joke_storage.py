import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import pytest
import os

def main():
    """Run tests with coverage report"""
    # Set AWS environment variables
    os.environ['AWS_DEFAULT_REGION'] = 'ap-southeast-2'
    os.environ['AWS_ACCESS_KEY_ID'] = 'test'
    os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'
    os.environ['DYNAMODB_TABLE'] = 'funny-weather-entries'
    os.environ['DYNAMODB_ENDPOINT_URL'] = 'http://localhost:4566'

    # Run pytest with coverage
    pytest.main(['tests/', '--verbose', '--cov=app', '--cov-report=term-missing'])

if __name__ == "__main__":
    main() 