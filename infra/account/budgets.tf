locals {
  budget_name = "personal-website-monthly"
  # Actual-spend alerts only, no forecast alert (spec, 2026-10-06).
  budget_alert_thresholds = [80, 100]
}

resource "aws_budgets_budget" "prod" {
  provider     = aws.prod
  name         = local.budget_name
  budget_type  = "COST"
  limit_amount = tostring(var.budget_amount)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  dynamic "notification" {
    for_each = local.budget_alert_thresholds
    content {
      notification_type          = "ACTUAL"
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      subscriber_email_addresses = [var.budget_email]
    }
  }
}

resource "aws_budgets_budget" "dev" {
  provider     = aws.dev
  name         = local.budget_name
  budget_type  = "COST"
  limit_amount = tostring(var.budget_amount)
  limit_unit   = "USD"
  time_unit    = "MONTHLY"

  dynamic "notification" {
    for_each = local.budget_alert_thresholds
    content {
      notification_type          = "ACTUAL"
      comparison_operator        = "GREATER_THAN"
      threshold                  = notification.value
      threshold_type             = "PERCENTAGE"
      subscriber_email_addresses = [var.budget_email]
    }
  }
}
