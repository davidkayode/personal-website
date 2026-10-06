mock_provider "aws" {
  alias = "mgmt"
  mock_data "aws_caller_identity" {
    defaults = { account_id = "111111111111" }
  }
  mock_data "aws_ssoadmin_instances" {
    defaults = {
      arns               = ["arn:aws:sso:::instance/ssoins-0000000000000000"]
      identity_store_ids = ["d-0000000000"]
    }
  }
}

mock_provider "aws" {
  alias = "prod"
  mock_data "aws_caller_identity" {
    defaults = { account_id = "222222222222" }
  }
}

mock_provider "aws" {
  alias = "dev"
  mock_data "aws_caller_identity" {
    defaults = { account_id = "333333333333" }
  }
}

override_data {
  target = data.aws_identitystore_group.admin
  values = { group_id = "aaaaaaaa-0000-0000-0000-000000000001" }
}

override_data {
  target = data.aws_identitystore_group.developer
  values = { group_id = "aaaaaaaa-0000-0000-0000-000000000002" }
}

variables {
  budget_email = "alerts@example.com"
}

run "account_config" {
  command = plan

  assert {
    condition     = aws_budgets_budget.prod.name == "personal-website-monthly" && aws_budgets_budget.dev.name == "personal-website-monthly"
    error_message = "Both budgets must be named personal-website-monthly."
  }
  assert {
    condition     = alltrue([for b in [aws_budgets_budget.prod, aws_budgets_budget.dev] : b.limit_amount == "1" && b.limit_unit == "USD" && b.time_unit == "MONTHLY" && b.budget_type == "COST"])
    error_message = "Both budgets must be $1 USD monthly cost budgets."
  }
  assert {
    condition     = alltrue([for b in [aws_budgets_budget.prod, aws_budgets_budget.dev] : length(b.notification) == 2])
    error_message = "Each budget must have exactly two notifications."
  }
  assert {
    condition     = alltrue([for b in [aws_budgets_budget.prod, aws_budgets_budget.dev] : toset([for n in b.notification : n.threshold]) == toset([80, 100])])
    error_message = "Budget alerts must fire at 80% and 100%."
  }
  assert {
    condition     = alltrue(flatten([for b in [aws_budgets_budget.prod, aws_budgets_budget.dev] : [for n in b.notification : n.notification_type == "ACTUAL" && n.comparison_operator == "GREATER_THAN" && n.threshold_type == "PERCENTAGE"]]))
    error_message = "Budget alerts must be actual-spend percentage alerts. There is no forecast alert."
  }
  assert {
    condition     = alltrue(flatten([for b in [aws_budgets_budget.prod, aws_budgets_budget.dev] : [for n in b.notification : n.subscriber_email_addresses == toset(["alerts@example.com"])]]))
    error_message = "Every alert must go only to var.budget_email."
  }
  assert {
    condition     = aws_ssoadmin_permission_set.administrator.name == "Administrator" && aws_ssoadmin_permission_set.administrator.session_duration == "PT1H"
    error_message = "Administrator must have a one-hour session."
  }
  assert {
    condition     = aws_ssoadmin_permission_set.developer.name == "Developer" && aws_ssoadmin_permission_set.developer.session_duration == "PT12H"
    error_message = "Developer must have a twelve-hour session."
  }
  assert {
    condition     = aws_ssoadmin_managed_policy_attachment.administrator.managed_policy_arn == "arn:aws:iam::aws:policy/AdministratorAccess" && aws_ssoadmin_managed_policy_attachment.developer.managed_policy_arn == "arn:aws:iam::aws:policy/PowerUserAccess"
    error_message = "Administrator gets AdministratorAccess and Developer gets PowerUserAccess."
  }
  assert {
    condition     = toset([for a in aws_ssoadmin_account_assignment.administrator : a.target_id]) == toset(["111111111111", "222222222222", "333333333333"]) && alltrue([for a in aws_ssoadmin_account_assignment.administrator : a.principal_id == "aaaaaaaa-0000-0000-0000-000000000001" && a.principal_type == "GROUP"])
    error_message = "The Admin group must be assigned Administrator in all three accounts."
  }
  assert {
    condition     = toset([for a in aws_ssoadmin_account_assignment.developer : a.target_id]) == toset(["222222222222", "333333333333"]) && alltrue([for a in aws_ssoadmin_account_assignment.developer : a.principal_id == "aaaaaaaa-0000-0000-0000-000000000002"])
    error_message = "The Developer group must be assigned Developer in prod and dev only."
  }
}

run "rejects_a_malformed_email" {
  command = plan
  variables {
    budget_email = "not-an-email"
  }
  expect_failures = [var.budget_email]
}
