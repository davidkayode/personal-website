provider "aws" {
  region = "us-east-1"
}

# The davidkayode.com zone lives in the management account.
provider "aws" {
  alias  = "dns"
  region = "us-east-1"

  assume_role {
    role_arn = var.dns_role_arn
  }
}
