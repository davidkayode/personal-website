#!/usr/bin/env bash
# Stage 4: roles in the management account that let prod Terraform manage the
# davidkayode.com zone, plus the plan role's permission to use the read-only one.
# Run: MGMT_PROFILE=admin PROD_PROFILE=prod-admin ZONE_ID=<zone id> infra/bootstrap/dns-roles.sh
set -euo pipefail
cd "$(dirname "$0")"
: "${MGMT_PROFILE:?}" "${PROD_PROFILE:?}" "${ZONE_ID:?}"
ACCOUNT_ID=$(aws sts get-caller-identity --profile "$PROD_PROFILE" --query Account --output text)
MGMT_ACCOUNT_ID=$(aws sts get-caller-identity --profile "$MGMT_PROFILE" --query Account --output text)

render() {
  sed -e "s/@ACCOUNT_ID@/${ACCOUNT_ID}/g" -e "s/@MGMT_ACCOUNT_ID@/${MGMT_ACCOUNT_ID}/g" -e "s/@ZONE_ID@/${ZONE_ID}/g" "policies/$1"
}

upsert_role() { # name trust-template policy-template
  if aws iam get-role --role-name "$1" --profile "$MGMT_PROFILE" >/dev/null 2>&1; then
    aws iam update-assume-role-policy --role-name "$1" --policy-document "$(render "$2")" --profile "$MGMT_PROFILE"
  else
    aws iam create-role --role-name "$1" --assume-role-policy-document "$(render "$2")" --profile "$MGMT_PROFILE" >/dev/null
  fi
  aws iam put-role-policy --role-name "$1" --policy-name "$1" --policy-document "$(render "$3")" --profile "$MGMT_PROFILE"
  aws iam get-role --role-name "$1" --profile "$MGMT_PROFILE" --query Role.Arn --output text
}

upsert_role personal-website-dns dns-trust.json dns-policy.json
upsert_role personal-website-dns-read dns-read-trust.json dns-read-policy.json
aws iam put-role-policy --role-name GitHub_Plan_Role --policy-name assume-dns-read \
  --policy-document "$(render plan-assume-dns.json)" --profile "$PROD_PROFILE"
