mock_provider "aws" {
  mock_data "aws_caller_identity" {
    defaults = {
      account_id = "123456789012"
    }
  }

  # The provider validates ARN-typed arguments, so wired-together ARNs need a real shape.
  mock_resource "aws_iam_role" {
    defaults = {
      arn = "arn:aws:iam::123456789012:role/personal-website-counter"
    }
  }
  mock_resource "aws_cloudwatch_log_group" {
    defaults = {
      arn = "arn:aws:logs:us-east-1:123456789012:log-group:/aws/test"
    }
  }
  mock_resource "aws_apigatewayv2_api" {
    defaults = {
      execution_arn = "arn:aws:execute-api:us-east-1:123456789012:abc123"
    }
  }
  mock_resource "aws_dynamodb_table" {
    defaults = {
      arn = "arn:aws:dynamodb:us-east-1:123456789012:table/personal-website-visitors"
    }
  }
}

run "counter_stack" {
  command = apply

  assert {
    condition     = aws_lambda_function.counter.runtime == "python3.12"
    error_message = "The counter Lambda must run on python3.12."
  }
  assert {
    condition     = aws_lambda_function.counter.handler == "handler.lambda_handler"
    error_message = "The handler must be handler.lambda_handler."
  }
  assert {
    condition     = aws_lambda_function.counter.environment[0].variables.TABLE_NAME == aws_dynamodb_table.visitors.name
    error_message = "The Lambda must receive the table name as TABLE_NAME."
  }
  assert {
    condition     = aws_dynamodb_table.visitors.name == "personal-website-visitors" && aws_dynamodb_table.visitors.billing_mode == "PAY_PER_REQUEST" && aws_dynamodb_table.visitors.deletion_protection_enabled
    error_message = "The visitors table must be on-demand with deletion protection."
  }
  assert {
    condition     = toset(aws_apigatewayv2_api.counter.cors_configuration[0].allow_origins) == toset(["https://davidkayode.com", "https://www.davidkayode.com"])
    error_message = "CORS must allow exactly the apex and www origins."
  }
  assert {
    condition     = toset(aws_apigatewayv2_api.counter.cors_configuration[0].allow_methods) == toset(["POST"])
    error_message = "CORS must allow only POST."
  }
  assert {
    condition     = aws_apigatewayv2_route.count.route_key == "POST /count"
    error_message = "The counter route must be POST /count."
  }
  assert {
    condition     = aws_apigatewayv2_stage.prod.name == "prod" && aws_apigatewayv2_stage.prod.default_route_settings[0].throttling_burst_limit == 10 && aws_apigatewayv2_stage.prod.default_route_settings[0].throttling_rate_limit == 5
    error_message = "The prod stage must throttle at burst 10, rate 5."
  }
  assert {
    condition     = jsonencode([for s in jsondecode(aws_iam_role_policy.counter.policy).Statement : s.Action if s.Sid == "IncrementCounter"][0]) == jsonencode(["dynamodb:UpdateItem"])
    error_message = "The counter role may only call dynamodb:UpdateItem on the table."
  }
  assert {
    condition     = endswith(aws_iam_role.counter.permissions_boundary, ":policy/personal-website-lambda-boundary")
    error_message = "The counter role must carry the personal-website-lambda-boundary permissions boundary."
  }
  assert {
    condition     = endswith(output.api_url, "/count")
    error_message = "api_url must point at the /count route."
  }
}
