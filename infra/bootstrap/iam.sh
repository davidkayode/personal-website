#!/usr/bin/env bash
# One-time IAM setup in the prod account: Lambda permissions boundary, the deploy
# policy on GitHub_Role, and the read-only GitHub_Plan_Role.
# Run: AWS_PROFILE=prod-admin MGMT_ACCOUNT_ID=<management account id> infra/bootstrap/iam.sh
set -euo pipefail
cd "$(dirname "$0")"
: "${MGMT_ACCOUNT_ID:?set MGMT_ACCOUNT_ID}"
ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
STATE_BUCKET=${STATE_BUCKET:-davidkayode-personal-website-tfstate}

render() {
  sed -e "s/@ACCOUNT_ID@/${ACCOUNT_ID}/g" \
      -e "s/@MGMT_ACCOUNT_ID@/${MGMT_ACCOUNT_ID}/g" \
      -e "s/@STATE_BUCKET@/${STATE_BUCKET}/g" "policies/$1"
}

boundary_arn="arn:aws:iam::${ACCOUNT_ID}:policy/personal-website-lambda-boundary"
canonical() { python3 -c 'import json,sys; print(json.dumps(json.load(sys.stdin), sort_keys=True))'; }

if aws iam get-policy --policy-arn "$boundary_arn" >/dev/null 2>&1; then
  default_version=$(aws iam get-policy --policy-arn "$boundary_arn" --query Policy.DefaultVersionId --output text)
  live=$(aws iam get-policy-version --policy-arn "$boundary_arn" --version-id "$default_version" --query PolicyVersion.Document --output json | canonical)
  wanted=$(render lambda-boundary.json | canonical)
  if [ "$live" != "$wanted" ]; then
    # IAM keeps at most five versions: drop the oldest non-default one first.
    if [ "$(aws iam list-policy-versions --policy-arn "$boundary_arn" --query 'length(Versions)' --output text)" -ge 5 ]; then
      oldest=$(aws iam list-policy-versions --policy-arn "$boundary_arn" --query 'sort_by(Versions[?!IsDefaultVersion], &CreateDate)[0].VersionId' --output text)
      aws iam delete-policy-version --policy-arn "$boundary_arn" --version-id "$oldest"
    fi
    aws iam create-policy-version --policy-arn "$boundary_arn" \
      --policy-document "$(render lambda-boundary.json)" --set-as-default >/dev/null
  fi
else
  aws iam create-policy --policy-name personal-website-lambda-boundary \
    --policy-document "$(render lambda-boundary.json)" >/dev/null
fi

aws iam put-role-policy --role-name GitHub_Role --policy-name personal-website-deploy \
  --policy-document "$(render deploy.json)"

if aws iam get-role --role-name GitHub_Plan_Role >/dev/null 2>&1; then
  aws iam update-assume-role-policy --role-name GitHub_Plan_Role --policy-document "$(render plan-trust.json)"
else
  aws iam create-role --role-name GitHub_Plan_Role --assume-role-policy-document "$(render plan-trust.json)" >/dev/null
fi
# PR plans run branch code, so they get only the reads terraform plan needs (no ReadOnlyAccess).
aws iam put-role-policy --role-name GitHub_Plan_Role --policy-name personal-website-plan --policy-document "$(render plan.json)"
aws iam detach-role-policy --role-name GitHub_Plan_Role --policy-arn arn:aws:iam::aws:policy/ReadOnlyAccess 2>/dev/null || true

echo "boundary:  $boundary_arn"
echo "plan role: $(aws iam get-role --role-name GitHub_Plan_Role --query Role.Arn --output text)"
