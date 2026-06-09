variable "aws_region" {
  description = "Primary AWS region for regional resources."
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Short project/name prefix for resources."
  type        = string
  default     = "miraomics"
}

variable "environment" {
  description = "Deployment environment (prod, staging, ...)."
  type        = string
  default     = "prod"
}

# DNS / domains ---------------------------------------------------------------
variable "domain_name" {
  description = "Apex domain, e.g. miraomics.bio."
  type        = string
  default     = "miraomics.bio"
}

variable "site_subdomain" {
  description = "Primary site host. Empty string serves the apex."
  type        = string
  default     = "www"
}

variable "api_subdomain" {
  description = "Subdomain for the form/track/dashboard API."
  type        = string
  default     = "api"
}

variable "route53_zone_id" {
  description = "Route53 hosted zone ID for domain_name. Leave empty to skip DNS + ACM automation (manage records manually)."
  type        = string
  default     = ""
}

# Forms / notifications -------------------------------------------------------
variable "notify_email" {
  description = "Address that receives lead notifications."
  type        = string
  default     = ""
}

variable "ses_from_email" {
  description = "Verified SES sender for notifications. Leave empty to disable email (leads still stored)."
  type        = string
  default     = ""
}

variable "verify_ses_from_identity" {
  description = "If true, create + verify the ses_from_email as an SES email identity (requires clicking the verification link)."
  type        = bool
  default     = false
}

# Dashboard auth (Cognito) ----------------------------------------------------
variable "cognito_domain_prefix" {
  description = "Globally-unique prefix for the Cognito Hosted UI domain (<prefix>.auth.<region>.amazoncognito.com)."
  type        = string
  default     = "miraomics-auth"
}

variable "admin_emails" {
  description = "Emails seeded as dashboard admin users (small team). Cognito emails each a temporary password."
  type        = list(string)
  default     = []
}

# CI/CD (GitHub OIDC) ---------------------------------------------------------
variable "github_repo" {
  description = "GitHub repo allowed to assume the deploy role, as owner/name."
  type        = string
  default     = "honicky/fun-with-lean"
}

variable "github_branch" {
  description = "Branch allowed to assume the deploy role (apply/deploy)."
  type        = string
  default     = "main"
}

variable "tags" {
  description = "Extra tags applied to all resources."
  type        = map(string)
  default     = {}
}
