variable "name" {
  type        = string
  description = "Resource name prefix."
}

variable "region" {
  type        = string
  description = "AWS region."
}

variable "allowed_origin" {
  type        = string
  description = "CORS origin for browser calls (the site URL)."
}

variable "notify_email" {
  type        = string
  description = "Recipient for lead notifications. Empty disables email."
  default     = ""
}

variable "ses_from_email" {
  type        = string
  description = "Verified SES sender. Empty disables email."
  default     = ""
}

variable "verify_ses_from_identity" {
  type        = bool
  description = "Create+verify ses_from_email as an SES email identity."
  default     = false
}

variable "cognito_issuer" {
  type        = string
  description = "Cognito OIDC issuer for the JWT authorizer."
}

variable "cognito_client_id" {
  type        = string
  description = "Cognito app client id (JWT audience)."
}

variable "pageview_ttl_days" {
  type        = number
  description = "Retention for pageview rows."
  default     = 400
}

# Optional custom domain for the API ----------------------------------------
variable "domain_name" {
  type    = string
  default = ""
}
variable "api_subdomain" {
  type    = string
  default = "api"
}
variable "route53_zone_id" {
  type    = string
  default = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
