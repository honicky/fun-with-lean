variable "name" {
  type        = string
  description = "Resource name prefix."
}

variable "github_repo" {
  type        = string
  description = "owner/name of the GitHub repository."
}

variable "github_branch" {
  type        = string
  description = "Branch permitted to deploy (apply)."
  default     = "main"
}

variable "create_oidc_provider" {
  type        = bool
  description = "Create the GitHub OIDC provider. Set false if the account already has one."
  default     = true
}

variable "state_bucket" {
  type        = string
  description = "Terraform state bucket the role may access."
  default     = ""
}

variable "state_lock_table" {
  type        = string
  description = "Terraform lock table the role may access."
  default     = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
