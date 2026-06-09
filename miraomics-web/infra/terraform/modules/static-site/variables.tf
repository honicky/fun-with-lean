variable "name" {
  description = "Resource name prefix."
  type        = string
}

variable "domain_name" {
  description = "Apex domain (miraomics.bio)."
  type        = string
}

variable "site_subdomain" {
  description = "Primary host subdomain; empty serves the apex."
  type        = string
  default     = "www"
}

variable "route53_zone_id" {
  description = "Hosted zone ID. Empty disables DNS + ACM automation."
  type        = string
  default     = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
