#!/usr/bin/env bash
# Plan or deploy one Terraform stack under infra/<stack>.
# Usage: scripts/tf-stack.sh plan|deploy <stack>
# Needs: TF_STATE_BUCKET, AWS_REGION. Optional: ALLOW_DESTROY=true.
set -euo pipefail
mode=$1
stack=$2
dir="infra/${stack}"

terraform -chdir="$dir" init -input=false -no-color \
  -backend-config="bucket=${TF_STATE_BUCKET}" \
  -backend-config="key=personal-website/${stack}.tfstate" \
  -backend-config="region=${AWS_REGION}"

if [ "$mode" = "plan" ]; then
  terraform -chdir="$dir" plan -input=false -no-color -lock=false | tee "plan-${stack}.txt"
  exit "${PIPESTATUS[0]}"
fi

set +e
terraform -chdir="$dir" plan -input=false -no-color -detailed-exitcode -out=tfplan
code=$?
set -e
case "$code" in
  0) echo "${stack}: no changes"; exit 0 ;;
  2) ;;
  *) exit "$code" ;;
esac

terraform -chdir="$dir" show -json tfplan > "${dir}/tfplan.json"
if [ "${ALLOW_DESTROY:-false}" != "true" ]; then
  python3 scripts/refuse_destructive_plan.py "${dir}/tfplan.json"
fi
terraform -chdir="$dir" apply -input=false -no-color tfplan
