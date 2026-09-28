#!/usr/bin/env bash
# One-time: create the Terraform state bucket in the prod account.
# Run: AWS_PROFILE=prod-admin infra/bootstrap/state-bucket.sh
set -euo pipefail
B=davidkayode-personal-website-tfstate
if ! aws s3api head-bucket --bucket "$B" 2>/dev/null; then
  aws s3api create-bucket --bucket "$B" --region us-east-1
fi
aws s3api put-public-access-block --bucket "$B" --public-access-block-configuration \
  BlockPublicAcls=true,IgnorePublicAcls=true,BlockPublicPolicy=true,RestrictPublicBuckets=true
aws s3api put-bucket-versioning --bucket "$B" --versioning-configuration Status=Enabled
aws s3api put-bucket-encryption --bucket "$B" --server-side-encryption-configuration \
  '{"Rules":[{"ApplyServerSideEncryptionByDefault":{"SSEAlgorithm":"AES256"}}]}'
aws s3api put-bucket-policy --bucket "$B" --policy "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Sid\":\"TLSOnly\",\"Effect\":\"Deny\",\"Principal\":\"*\",\"Action\":\"s3:*\",\"Resource\":[\"arn:aws:s3:::$B\",\"arn:aws:s3:::$B/*\"],\"Condition\":{\"Bool\":{\"aws:SecureTransport\":\"false\"}}}]}"
echo "state bucket ready: $B"
