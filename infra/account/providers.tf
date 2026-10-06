provider "aws" {
  alias   = "mgmt"
  region  = "us-east-1"
  profile = var.mgmt_profile
}

provider "aws" {
  alias   = "prod"
  region  = "us-east-1"
  profile = var.prod_profile
}

provider "aws" {
  alias   = "dev"
  region  = "us-east-1"
  profile = var.dev_profile
}
