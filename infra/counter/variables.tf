variable "project" {
  description = "Prefix for every resource name."
  type        = string
  default     = "personal-website"
}

variable "site_origins" {
  description = "Browser origins allowed to call the counter API."
  type        = list(string)
  default     = ["https://davidkayode.com", "https://www.davidkayode.com"]
}

