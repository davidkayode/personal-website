variable "mgmt_profile" {
  description = "SSO profile for the management account."
  type        = string
  default     = "admin"
}

variable "prod_profile" {
  description = "SSO profile for the prod account."
  type        = string
  default     = "prod-admin"
}

variable "dev_profile" {
  description = "SSO profile for the dev account."
  type        = string
  default     = "dev-admin"
}

variable "budget_email" {
  description = "Where budget alerts go. Set in the gitignored terraform.tfvars."
  type        = string

  validation {
    condition     = can(regex("^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$", var.budget_email))
    error_message = "budget_email must be an email address."
  }
}

variable "budget_amount" {
  description = "Monthly budget per account, in USD."
  type        = number
  default     = 1
}
