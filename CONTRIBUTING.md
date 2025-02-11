# Contributing to Funny Weather

Welcome! We're excited that you want to contribute to Funny Weather. This document will guide you through setting up your local development environment and our contribution process.

## Local Development Setup

### Prerequisites

- Python 3.11+
- Docker and Docker Compose
- AWS CLI
- Terraform 1.5.0+
- An OpenAI API key
- A MetService API key

### Initial Setup

1. Clone the repository:
```bash
git clone https://github.com/robertoallende/funny-weather.git
cd funny-weather
```

2. Create a Python virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
# Create .env file
cat > .env << EOL
AWS_ACCESS_KEY_ID=test
AWS_SECRET_ACCESS_KEY=test
AWS_DEFAULT_REGION=ap-southeast-2
LOCALSTACK_HOSTNAME=localhost
EOL

# Source the environment variables
source .env
```

4. Create Terraform variables file:
```bash
# Create infrastructure/terraform.tfvars
cat > infrastructure/terraform.tfvars << EOL
met_api_key = "your-metservice-api-key"
openai_api_key = "your-openai-api-key"
EOL
```

### Starting the Local Environment

1. Start LocalStack:
```bash
docker-compose up -d
```

2. Initialize and apply Terraform:
```bash
cd infrastructure
terraform init
terraform apply
```

3. Insert test data:
```bash
python scripts/insert_test_data.py
```

### Testing the Components

1. Test the Weather Fetcher:
```bash
cd src/lambdas/weather_fetcher/scripts
python test_lambda.py
```

2. Test the Joke Generator:
```bash
cd src/lambdas/joke_generator/scripts
python test_joke_generator.py
```

3. Test the API:
```bash
cd src/lambdas/get_funny_weather/scripts
./run_local.sh
```

The API will be available at `http://localhost:8000/weather`

### Running Tests

Run all tests with coverage:
```bash
pytest tests/ --cov=src --cov-report=term-missing
```

## Development Workflow

1. Create a new branch for your feature:
```bash
git checkout -b feature/your-feature-name
```

2. Make your changes and write tests

3. Run the test suite:
```bash
pytest
```

4. Run the linter:
```bash
flake8 src tests
```

5. Commit your changes:
```bash
git add .
git commit -m "feat: description of your changes"
```

We follow [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

## Project Structure

```
funny-weather/
├── infrastructure/        # Terraform configuration
├── src/
│   └── lambdas/          # Lambda functions
│       ├── weather_fetcher/
│       ├── joke_generator/
│       ├── weather_storage/
│       └── get_funny_weather/
├── tests/                # Integration tests
└── docker-compose.yml    # Local development services
```

## Debugging

### Common Issues

1. LocalStack Connection Issues:
```bash
# Check if LocalStack is running
docker ps

# Check LocalStack logs
docker logs localstack_demo
```

2. DynamoDB Issues:
```bash
# List tables
aws dynamodb list-tables --endpoint-url=http://localhost:4566

# Scan table contents
aws dynamodb scan --table-name funny-weather-entries --endpoint-url=http://localhost:4566
```

3. Lambda Issues:
```bash
# Test Lambda function locally
aws lambda invoke --function-name weather-fetcher \
    --endpoint-url=http://localhost:4566 \
    --payload '{"location":"Wellington"}' \
    output.json
```

### Useful Commands

- Reset LocalStack:
```bash
docker-compose down -v
docker-compose up -d
```

- Clean Python cache:
```bash
find . -type d -name "__pycache__" -exec rm -r {} +
```

## CI/CD Pipeline

Our GitHub Actions workflow runs on every push and pull request:
1. Runs tests
2. Performs integration tests with LocalStack
3. Deploys to AWS (on main branch only)

## Need Help?

- Check existing issues or create a new one
- Join our discussions
- Contact the maintainers

## Code of Conduct

Please read our [Code of Conduct](CODE_OF_CONDUCT.md) before contributing.

## License

By contributing, you agree that your contributions will be licensed under the MIT License. 