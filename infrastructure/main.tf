provider "aws" {
    region = "ap-southeast-2"
}
  
# Create IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "weather-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}
  
# Allow Lambda to publish to EventBridge
resource "aws_iam_role_policy" "lambda_eventbridge" {
  name = "lambda-eventbridge-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "events:PutEvents"
        ]
        Resource = "*"
      }
    ]
  })
}
  
# Create local directory for build
resource "local_file" "build_dir" {
  content  = ""
  filename = "${path.module}/build/weather_fetcher/.keep"

  lifecycle {
    create_before_destroy = true
  }
}
  
# Install dependencies for weather fetcher Lambda
resource "null_resource" "weather_lambda_deps" {
  provisioner "local-exec" {
    command = "bash scripts/build_lambda.sh"
    working_dir = path.module
  }

  triggers = {
    dependencies_versions = filemd5("${path.module}/../src/lambdas/weather_fetcher/requirements.txt")
    source_code = filemd5("${path.module}/../src/lambdas/weather_fetcher/app.py")
    timestamp = timestamp()
  }

  depends_on = [local_file.build_dir]
}
  
# Package weather fetcher Lambda
data "archive_file" "weather_fetcher" {
  type        = "zip"
  source_dir  = "${path.module}/build/weather_fetcher"
  output_path = "${path.module}/files/weather_fetcher.zip"
  
  depends_on = [null_resource.weather_lambda_deps]
}
  
# Create local directory for joke generator build
resource "local_file" "joke_build_dir" {
  content  = ""
  filename = "${path.module}/build/joke_generator/.keep"

  lifecycle {
    create_before_destroy = true
  }
}
  
# Install dependencies for joke generator Lambda
resource "null_resource" "joke_lambda_deps" {
  provisioner "local-exec" {
    command = "bash scripts/build_joke_lambda.sh"
    working_dir = path.module
  }

  triggers = {
    dependencies_versions = filemd5("${path.module}/../src/lambdas/joke_generator/requirements.txt")
    source_code = filemd5("${path.module}/../src/lambdas/joke_generator/app.py")
    timestamp = timestamp()
  }

  depends_on = [local_file.joke_build_dir]
}
  
# Package joke generator Lambda
data "archive_file" "joke_generator" {
  type        = "zip"
  source_dir  = "${path.module}/build/joke_generator"
  output_path = "${path.module}/files/joke_generator.zip"
  
  depends_on = [null_resource.joke_lambda_deps]
}
  
# Create weather fetcher Lambda
resource "aws_lambda_function" "weather_fetcher" {
  filename         = data.archive_file.weather_fetcher.output_path
  source_code_hash = data.archive_file.weather_fetcher.output_base64sha256
  function_name    = "weather-fetcher"
  role            = aws_iam_role.lambda_role.arn
  handler         = "app.handler"
  runtime         = "python3.11"
  timeout         = 30  # Increased timeout to handle potential API delays
  memory_size     = 256 # Increased memory for numpy operations

  environment {
    variables = {
      MET_API_KEY = var.met_api_key  # Use variable instead of hardcoded value
    }
  }
}
  
# Create joke generator Lambda
resource "aws_lambda_function" "joke_generator" {
  filename         = data.archive_file.joke_generator.output_path
  source_code_hash = data.archive_file.joke_generator.output_base64sha256
  function_name    = "joke-generator"
  role            = aws_iam_role.lambda_role.arn
  handler         = "app.handler"
  runtime         = "python3.11"
  timeout         = 60  # Increase timeout to 60 seconds
  memory_size     = 512  # Increase memory for better performance

  environment {
    variables = {
      OPENAI_API_KEY = aws_secretsmanager_secret_version.api_keys.secret_string
      POWERTOOLS_SERVICE_NAME = "joke-generator"
      LOG_LEVEL = "DEBUG"
    }
  }
}

# Create local directory for storage Lambda build
resource "local_file" "storage_build_dir" {
  content  = ""
  filename = "${path.module}/build/weather_storage/.keep"

  lifecycle {
    create_before_destroy = true
  }
}

# Install dependencies for storage Lambda
resource "null_resource" "storage_lambda_deps" {
  provisioner "local-exec" {
    command = "bash scripts/build_storage_lambda.sh"
    working_dir = path.module
  }

  triggers = {
    dependencies_versions = filemd5("${path.module}/../src/lambdas/weather_storage/requirements.txt")
    source_code = filemd5("${path.module}/../src/lambdas/weather_storage/app.py")
    timestamp = timestamp()
  }

  depends_on = [local_file.storage_build_dir]
}

# Package storage Lambda
data "archive_file" "weather_storage" {
  type        = "zip"
  source_dir  = "${path.module}/build/weather_storage"
  output_path = "${path.module}/files/weather_storage.zip"
  
  depends_on = [null_resource.storage_lambda_deps]
}

# Create weather storage Lambda
resource "aws_lambda_function" "weather_storage" {
  filename         = data.archive_file.weather_storage.output_path
  source_code_hash = data.archive_file.weather_storage.output_base64sha256
  function_name    = "weather-storage"
  role            = aws_iam_role.lambda_role.arn
  handler         = "app.handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.weather_entries.name
    }
  }
}

# Add DynamoDB permissions to Lambda role
resource "aws_iam_role_policy" "lambda_dynamodb" {
  name = "lambda-dynamodb-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:GetItem",
          "dynamodb:UpdateItem",
          "dynamodb:Query",
          "dynamodb:Scan"
        ]
        Resource = [aws_dynamodb_table.weather_entries.arn]
      }
    ]
  })
}

# Create local directory for joke storage Lambda build
resource "local_file" "joke_storage_build_dir" {
  content  = ""
  filename = "${path.module}/build/joke_storage/.keep"

  lifecycle {
    create_before_destroy = true
  }
}

# Install dependencies for joke storage Lambda
resource "null_resource" "joke_storage_lambda_deps" {
  provisioner "local-exec" {
    command = "bash scripts/build_joke_storage_lambda.sh"
    working_dir = path.module
  }

  triggers = {
    dependencies_versions = filemd5("${path.module}/../src/lambdas/joke_storage/requirements.txt")
    source_code = filemd5("${path.module}/../src/lambdas/joke_storage/app.py")
    timestamp = timestamp()
  }

  depends_on = [local_file.joke_storage_build_dir]
}

# Package joke storage Lambda
data "archive_file" "joke_storage" {
  type        = "zip"
  source_dir  = "${path.module}/build/joke_storage"
  output_path = "${path.module}/files/joke_storage.zip"
  
  depends_on = [null_resource.joke_storage_lambda_deps]
}

# Create joke storage Lambda
resource "aws_lambda_function" "joke_storage" {
  filename         = data.archive_file.joke_storage.output_path
  source_code_hash = data.archive_file.joke_storage.output_base64sha256
  function_name    = "joke-storage"
  role            = aws_iam_role.lambda_role.arn
  handler         = "app.handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.weather_entries.name
    }
  }
}

# Create local directory for get funny weather Lambda build
resource "local_file" "get_funny_weather_build_dir" {
  content  = ""
  filename = "${path.module}/build/get_funny_weather/.keep"

  lifecycle {
    create_before_destroy = true
  }
}

# Install dependencies for get funny weather Lambda
resource "null_resource" "get_funny_weather_lambda_deps" {
  provisioner "local-exec" {
    command = "bash scripts/build_get_funny_weather_lambda.sh"
    working_dir = path.module
  }

  triggers = {
    dependencies_versions = filemd5("${path.module}/../src/lambdas/get_funny_weather/requirements.txt")
    source_code = filemd5("${path.module}/../src/lambdas/get_funny_weather/app.py")
    timestamp = timestamp()
  }

  depends_on = [local_file.get_funny_weather_build_dir]
}

# Package get funny weather Lambda
data "archive_file" "get_funny_weather" {
  type        = "zip"
  source_dir  = "${path.module}/build/get_funny_weather"
  output_path = "${path.module}/files/get_funny_weather.zip"
  
  depends_on = [null_resource.get_funny_weather_lambda_deps]
}

# Create get funny weather Lambda
resource "aws_lambda_function" "get_funny_weather" {
  filename         = data.archive_file.get_funny_weather.output_path
  source_code_hash = data.archive_file.get_funny_weather.output_base64sha256
  function_name    = "get-funny-weather"
  role            = aws_iam_role.lambda_role.arn
  handler         = "app.handler"
  runtime         = "python3.11"
  timeout         = 30
  memory_size     = 256

  environment {
    variables = {
      DYNAMODB_TABLE = aws_dynamodb_table.weather_entries.name
      POWERTOOLS_SERVICE_NAME = "get-funny-weather"
      LOG_LEVEL = "DEBUG"
    }
  }
}

# Add CloudWatch Logs permissions
resource "aws_iam_role_policy" "lambda_logs" {
  name = "lambda-logs-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      }
    ]
  })
}

# Add this to your Terraform configuration
resource "aws_secretsmanager_secret" "api_keys" {
  name = "funny-weather/api-keys"
}

resource "aws_secretsmanager_secret_version" "api_keys" {
  secret_id = aws_secretsmanager_secret.api_keys.id
  secret_string = jsonencode({
    met_api_key = var.met_api_key
    openai_api_key = var.openai_api_key
  })
}

# Update the Lambda role policy to allow access to secrets
resource "aws_iam_role_policy" "lambda_secrets" {
  name = "lambda-secrets-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue"
        ]
        Resource = [aws_secretsmanager_secret.api_keys.arn]
      }
    ]
  })
}

# Add CloudWatch Logs permissions to Lambda role
resource "aws_iam_role_policy_attachment" "lambda_cloudwatch" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role       = aws_iam_role.lambda_role.name
}