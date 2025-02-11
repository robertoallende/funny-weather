# API Gateway
resource "aws_api_gateway_rest_api" "funny_weather" {
  name = "funny-weather-api"
}

# API Gateway Resource
resource "aws_api_gateway_resource" "weather" {
  rest_api_id = aws_api_gateway_rest_api.funny_weather.id
  parent_id   = aws_api_gateway_rest_api.funny_weather.root_resource_id
  path_part   = "weather"
}

# API Gateway Method
resource "aws_api_gateway_method" "get_weather" {
  rest_api_id   = aws_api_gateway_rest_api.funny_weather.id
  resource_id   = aws_api_gateway_resource.weather.id
  http_method   = "GET"
  authorization = "NONE"
}

# API Gateway Integration
resource "aws_api_gateway_integration" "lambda" {
  rest_api_id = aws_api_gateway_rest_api.funny_weather.id
  resource_id = aws_api_gateway_resource.weather.id
  http_method = aws_api_gateway_method.get_weather.http_method

  integration_http_method = "POST"
  type                   = "AWS_PROXY"
  uri                    = aws_lambda_function.get_funny_weather.invoke_arn
}

# API Gateway Deployment
resource "aws_api_gateway_deployment" "funny_weather" {
  rest_api_id = aws_api_gateway_rest_api.funny_weather.id

  depends_on = [
    aws_api_gateway_integration.lambda
  ]

  lifecycle {
    create_before_destroy = true
  }
}

# API Gateway Stage
resource "aws_api_gateway_stage" "prod" {
  deployment_id = aws_api_gateway_deployment.funny_weather.id
  rest_api_id   = aws_api_gateway_rest_api.funny_weather.id
  stage_name    = "prod"
}

# Lambda Permission
resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_funny_weather.function_name
  principal     = "apigateway.amazonaws.com"

  source_arn = "${aws_api_gateway_rest_api.funny_weather.execution_arn}/*/*"
}

# Enable CORS
resource "aws_api_gateway_method" "weather_options" {
  rest_api_id   = aws_api_gateway_rest_api.funny_weather.id
  resource_id   = aws_api_gateway_resource.weather.id
  http_method   = "OPTIONS"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "weather_options" {
  rest_api_id = aws_api_gateway_rest_api.funny_weather.id
  resource_id = aws_api_gateway_resource.weather.id
  http_method = aws_api_gateway_method.weather_options.http_method
  type        = "MOCK"

  request_templates = {
    "application/json" = "{\"statusCode\": 200}"
  }
}

resource "aws_api_gateway_method_response" "weather_options_200" {
  rest_api_id = aws_api_gateway_rest_api.funny_weather.id
  resource_id = aws_api_gateway_resource.weather.id
  http_method = aws_api_gateway_method.weather_options.http_method
  status_code = "200"

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = true
    "method.response.header.Access-Control-Allow-Methods" = true
    "method.response.header.Access-Control-Allow-Origin"  = true
  }
}

resource "aws_api_gateway_integration_response" "weather_options" {
  rest_api_id = aws_api_gateway_rest_api.funny_weather.id
  resource_id = aws_api_gateway_resource.weather.id
  http_method = aws_api_gateway_method.weather_options.http_method
  status_code = aws_api_gateway_method_response.weather_options_200.status_code

  response_parameters = {
    "method.response.header.Access-Control-Allow-Headers" = "'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'"
    "method.response.header.Access-Control-Allow-Methods" = "'GET,OPTIONS'"
    "method.response.header.Access-Control-Allow-Origin"  = "'*'"
  }
}

# Output the API URL and ID for testing
output "api_endpoint" {
  value = "${aws_api_gateway_stage.prod.invoke_url}/weather"
}

output "rest_api_id" {
  value = aws_api_gateway_rest_api.funny_weather.id
} 