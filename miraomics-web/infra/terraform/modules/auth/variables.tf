variable "name" {
  type        = string
  description = "Resource name prefix."
}

variable "domain_prefix" {
  type        = string
  description = "Globally-unique Cognito Hosted UI prefix."
}

variable "region" {
  type        = string
  description = "AWS region (used to build the issuer + hosted UI URLs)."
}

variable "callback_urls" {
  type        = list(string)
  description = "Allowed OAuth callback URLs (dashboard /callback)."
}

variable "logout_urls" {
  type        = list(string)
  description = "Allowed post-logout redirect URLs."
}

variable "admin_emails" {
  type        = list(string)
  description = "Emails seeded as dashboard users."
  default     = []
}

variable "tags" {
  type    = map(string)
  default = {}
}
