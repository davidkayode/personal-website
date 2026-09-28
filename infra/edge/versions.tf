terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # bucket, key and region are passed with -backend-config by scripts/tf-stack.sh.
  backend "s3" {
    use_lockfile = true
    encrypt      = true
  }
}
