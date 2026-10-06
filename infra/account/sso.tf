data "aws_ssoadmin_instances" "this" {
  provider = aws.mgmt
}

data "aws_caller_identity" "mgmt" {
  provider = aws.mgmt
}

data "aws_caller_identity" "prod" {
  provider = aws.prod
}

data "aws_caller_identity" "dev" {
  provider = aws.dev
}

locals {
  instance_arn      = tolist(data.aws_ssoadmin_instances.this.arns)[0]
  identity_store_id = tolist(data.aws_ssoadmin_instances.this.identity_store_ids)[0]

  admin_accounts = {
    management = data.aws_caller_identity.mgmt.account_id
    prod       = data.aws_caller_identity.prod.account_id
    dev        = data.aws_caller_identity.dev.account_id
  }
  developer_accounts = {
    prod = data.aws_caller_identity.prod.account_id
    dev  = data.aws_caller_identity.dev.account_id
  }
}

# Groups and users stay hand-managed in Identity Center, so they're looked up by name.
data "aws_identitystore_group" "admin" {
  provider          = aws.mgmt
  identity_store_id = local.identity_store_id

  alternate_identifier {
    unique_attribute {
      attribute_path  = "DisplayName"
      attribute_value = "Admin"
    }
  }
}

data "aws_identitystore_group" "developer" {
  provider          = aws.mgmt
  identity_store_id = local.identity_store_id

  alternate_identifier {
    unique_attribute {
      attribute_path  = "DisplayName"
      attribute_value = "Developer"
    }
  }
}

# Administrator was imported from CloudFormation and must never be destroyed:
# every admin SSO profile, including the one that runs Terraform, depends on it.
resource "aws_ssoadmin_permission_set" "administrator" {
  provider         = aws.mgmt
  instance_arn     = local.instance_arn
  name             = "Administrator"
  description      = "Administrator access to AWS organization"
  session_duration = "PT1H"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_ssoadmin_managed_policy_attachment" "administrator" {
  provider           = aws.mgmt
  instance_arn       = local.instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.administrator.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/AdministratorAccess"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_ssoadmin_account_assignment" "administrator" {
  provider           = aws.mgmt
  for_each           = local.admin_accounts
  instance_arn       = local.instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.administrator.arn
  principal_id       = data.aws_identitystore_group.admin.group_id
  principal_type     = "GROUP"
  target_id          = each.value
  target_type        = "AWS_ACCOUNT"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_ssoadmin_permission_set" "developer" {
  provider         = aws.mgmt
  instance_arn     = local.instance_arn
  name             = "Developer"
  description      = "Developer access to AWS organization"
  session_duration = "PT12H"
}

resource "aws_ssoadmin_managed_policy_attachment" "developer" {
  provider           = aws.mgmt
  instance_arn       = local.instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.developer.arn
  managed_policy_arn = "arn:aws:iam::aws:policy/PowerUserAccess"
}

resource "aws_ssoadmin_account_assignment" "developer" {
  provider           = aws.mgmt
  for_each           = local.developer_accounts
  instance_arn       = local.instance_arn
  permission_set_arn = aws_ssoadmin_permission_set.developer.arn
  principal_id       = data.aws_identitystore_group.developer.group_id
  principal_type     = "GROUP"
  target_id          = each.value
  target_type        = "AWS_ACCOUNT"
}
