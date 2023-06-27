terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }

  required_version = ">= 1.4.6"
}


resource "aws_s3_bucket" "example" {
  bucket = ""

  tags = {
    Name        = "My bucket"
    Environment = "Dev"
  }
}

resource "aws_dynamodb_table" "basic-dynamodb-table" {
  name           = "websiteTable-iac"
  billing_mode   = "PROVISIONED"
  read_capacity  = 1
  write_capacity = 1
  hash_key       = "id"

  attribute {
    name = "id"
    type = "S"
  }

  tags = {
    Name        = "dynamodb-table-1"
    Environment = "Dev"
  }
}

data "aws_iam_policy_document" "assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "iam_for_lambda" {
  name               = "iam_for_lambda"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  role       = aws_iam_role.iam_for_lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "archive_file" "lambda" {
  type        = "zip"
  source_file = "lambda.py"
  output_path = "lambda_function_payload.zip"
}

resource "aws_lambda_function" "example" {
  # If the file is not in the current working directory you will need to include a
  # path.module in the filename.
  filename         = "lambda_function_payload.zip"
  function_name    = "visitorCounter-iac"
  role             = aws_iam_role.iam_for_lambda.arn
  handler          = "lambda.lambda_handler"
  runtime          = "python3.7"
  source_code_hash = data.archive_file.lambda.output_base64sha256
}

resource "aws_apigatewayv2_api" "example" {
  name          = "counterLambda-iac"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "example" {
  api_id      = aws_apigatewayv2_api.example.id
  name        = "example-stage"
  auto_deploy = true
}

resource "aws_apigatewayv2_integration" "example" {
  api_id             = aws_apigatewayv2_api.example.id
  integration_type   = "AWS_PROXY"
  connection_type    = "INTERNET"
  description        = "Lambda example"
  integration_method = "POST"
  integration_uri    = aws_lambda_function.example.invoke_arn
}

resource "aws_apigatewayv2_route" "visitor-counter" {
  api_id    = aws_apigatewayv2_api.example.id
  route_key = "POST /checkVisitorCounter"
  target    = "integrations/${aws_apigatewayv2_integration.example.id}"
}

resource "aws_cloudwatch_log_group" "api_gw" {
  name              = "/aws/api_gw/${aws_apigatewayv2_api.example.name}"
  retention_in_days = 30
}

resource "aws_lambda_permission" "api_gw" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.example.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.example.execution_arn}/*/*"
}

