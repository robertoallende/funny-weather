import boto3
import json
from datetime import datetime, timezone
from botocore.exceptions import ClientError

def setup_test_data():
    # Create DynamoDB client for LocalStack
    dynamodb = boto3.client(
        'dynamodb',
        endpoint_url='http://localhost:4566',
        region_name='ap-southeast-2',
        aws_access_key_id='test',
        aws_secret_access_key='test'
    )

    # Create table if it doesn't exist
    try:
        dynamodb.describe_table(TableName='funny-weather-entries')
        print("Table already exists")
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceNotFoundException':
            print("Creating table...")
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
            # Wait for table to be created
            print("Waiting for table to be created...")
            waiter = dynamodb.get_waiter('table_exists')
            waiter.wait(TableName='funny-weather-entries')
            print("Table created successfully")

    # Insert test data
    test_item = {
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

    try:
        dynamodb.put_item(
            TableName='funny-weather-entries',
            Item=test_item
        )
        print("Test data inserted successfully")
    except Exception as e:
        print(f"Error inserting test data: {str(e)}")

if __name__ == "__main__":
    setup_test_data() 