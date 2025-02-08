provider "aws" {
    region                      = "ap-southeast-2"
    access_key                  = "test"
    secret_key                  = "test"
    skip_credentials_validation = true
    skip_requesting_account_id  = true
    skip_metadata_api_check     = true
  
    # LocalStack endpoint
    endpoints {
      lambda     = "http://localhost:4566"
      events     = "http://localhost:4566"
      scheduler  = "http://localhost:4566"
      iam        = "http://localhost:4566"
    }
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
          Resource = ["*"]
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
    timeout         = 30
    memory_size     = 256

    environment {
      variables = {
        OPENAI_API_KEY = var.openai_api_key
      }
    }
  }