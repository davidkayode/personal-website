terraform {
  required_version = ">= 1.10"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  # Applied by hand only. bucket, key and region are passed with -backend-config.
  backend "s3" {
    use_lockfile = true
    encrypt      = true
  }
}
