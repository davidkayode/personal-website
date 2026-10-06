# infra/account

Budgets (prod, dev) and IAM Identity Center permission sets and assignments (management). **Applied by hand only.** CI just runs `fmt`, `validate` and the mocked `terraform test`.

## Run it

Needs the `admin`, `prod-admin` and `dev-admin` SSO profiles, and a local `terraform.tfvars` (gitignored, backed up in the private docs repo):

```hcl
budget_email = "<where budget alerts go>"
```

```bash
aws sso login --profile admin
AWS_PROFILE=prod-admin TF_STATE_BUCKET=davidkayode-personal-website-tfstate AWS_REGION=us-east-1 \
  scripts/tf-stack.sh deploy account
```

Check that `budget_alert_recipient` in the plan output is the right address. A mistyped address still passes validation, and AWS sends no confirmation email.

## If the state is ever lost

**Never apply first.** Without state, Terraform would try to create the `Administrator` permission set and its assignments again. Every admin login depends on those.

1. Write a gitignored `imports.tf` with an `import` block for each resource. Look up the IDs live (`aws sso-admin list-instances`, `list-permission-sets`, `aws identitystore list-groups`, `aws sts get-caller-identity` per profile):
   - `aws_ssoadmin_permission_set.administrator` / `.developer` → `<permission set ARN>,<instance ARN>`
   - `aws_ssoadmin_managed_policy_attachment.<name>` → `<policy ARN>,<permission set ARN>,<instance ARN>`
   - `aws_ssoadmin_account_assignment.<name>["management"|"prod"|"dev"]` → `<group id>,GROUP,<account id>,AWS_ACCOUNT,<permission set ARN>,<instance ARN>`
   - `aws_budgets_budget.prod` / `.dev` → `<account id>:personal-website-monthly`
2. Run `terraform plan` and confirm it is import-only (`N to import, 0 to add, 0 to change, 0 to destroy`).
3. Apply, then delete `imports.tf`.

If you only need to recreate something that really is gone, use `-target` on that resource alone. Never run an untargeted apply against empty state.
