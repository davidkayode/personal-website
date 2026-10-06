data "aws_caller_identity" "current" {}

locals {
  counter_name        = "${var.project}-counter"
  lambda_boundary_arn = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:policy/${var.project}-lambda-boundary"
}

resource "aws_dynamodb_table" "visitors" {
  name                        = "${var.project}-visitors"
  billing_mode                = "PAY_PER_REQUEST"
  hash_key                    = "id"
  deletion_protection_enabled = true

  attribute {
    name = "id"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }
}

data "archive_file" "counter" {
  type        = "zip"
  source_file = "${path.module}/../../backend/counter/handler.py"
  output_path = "${path.module}/build/counter.zip"
}

resource "aws_cloudwatch_log_group" "counter" {
  name              = "/aws/lambda/${local.counter_name}"
  retention_in_days = 30
}

resource "aws_iam_role" "counter" {
  name                 = local.counter_name
  permissions_boundary = local.lambda_boundary_arn
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Action    = "sts:AssumeRole"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy" "counter" {
  name = local.counter_name
  role = aws_iam_role.counter.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "IncrementCounter"
        Effect   = "Allow"
        Action   = ["dynamodb:UpdateItem"]
        Resource = aws_dynamodb_table.visitors.arn
      },
      {
        Sid      = "ReadCounter"
        Effect   = "Allow"
        Action   = ["dynamodb:GetItem"]
        Resource = aws_dynamodb_table.visitors.arn
      },
      {
        Sid      = "WriteLogs"
        Effect   = "Allow"
        Action   = ["logs:CreateLogStream", "logs:PutLogEvents"]
        Resource = "${aws_cloudwatch_log_group.counter.arn}:*"
      },
    ]
  })
}

resource "aws_lambda_function" "counter" {
  function_name    = local.counter_name
  description      = "Visitor counter for davidkayode.com"
  role             = aws_iam_role.counter.arn
  runtime          = "python3.12"
  handler          = "handler.lambda_handler"
  filename         = data.archive_file.counter.output_path
  source_code_hash = data.archive_file.counter.output_base64sha256
  timeout          = 5
  memory_size      = 128

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.visitors.name
    }
  }

  depends_on = [aws_cloudwatch_log_group.counter, aws_iam_role_policy.counter]
}

resource "aws_apigatewayv2_api" "counter" {
  name          = "${var.project}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins = var.site_origins
    allow_methods = ["POST"]
    allow_headers = ["content-type"]
    max_age       = 3600
  }
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/apigateway/${var.project}-api"
  retention_in_days = 30
}

resource "aws_apigatewayv2_integration" "counter" {
  api_id                 = aws_apigatewayv2_api.counter.id
  integration_type       = "AWS_PROXY"
  integration_uri        = aws_lambda_function.counter.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "count" {
  api_id    = aws_apigatewayv2_api.counter.id
  route_key = "POST /count"
  target    = "integrations/${aws_apigatewayv2_integration.counter.id}"
}

# Read-only check for monitoring and the smoke test; it never counts a visit.
resource "aws_apigatewayv2_route" "health" {
  api_id    = aws_apigatewayv2_api.counter.id
  route_key = "GET /health"
  target    = "integrations/${aws_apigatewayv2_integration.counter.id}"
}

resource "aws_apigatewayv2_stage" "prod" {
  api_id      = aws_apigatewayv2_api.counter.id
  name        = "prod"
  auto_deploy = true

  default_route_settings {
    throttling_burst_limit = 10
    throttling_rate_limit  = 5
  }

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api.arn
    format = jsonencode({
      requestId = "$context.requestId"
      routeKey  = "$context.routeKey"
      status    = "$context.status"
      latencyMs = "$context.responseLatency"
    })
  }
}

resource "aws_lambda_permission" "api" {
  statement_id  = "AllowApiGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.counter.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.counter.execution_arn}/*/POST/count"
}

resource "aws_lambda_permission" "health" {
  statement_id  = "AllowApiGatewayHealth"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.counter.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.counter.execution_arn}/*/GET/health"
}
