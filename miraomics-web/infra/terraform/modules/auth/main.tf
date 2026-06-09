# Cognito user pool for the internal dashboard. Admin-create-only (no public
# sign-up) — a closed group of named users (requirement #7).
resource "aws_cognito_user_pool" "this" {
  name = "${var.name}-admins"

  username_attributes      = ["email"]
  auto_verified_attributes = ["email"]

  admin_create_user_config {
    allow_admin_create_user_only = true
  }

  password_policy {
    minimum_length                   = 12
    require_lowercase                = true
    require_uppercase                = true
    require_numbers                  = true
    require_symbols                  = true
    temporary_password_validity_days = 7
  }

  # MFA optional but available (TOTP) — encourage for an admin console.
  mfa_configuration = "OPTIONAL"
  software_token_mfa_configuration {
    enabled = true
  }

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  tags = var.tags
}

resource "aws_cognito_user_pool_domain" "this" {
  domain       = var.domain_prefix
  user_pool_id = aws_cognito_user_pool.this.id
}

resource "aws_cognito_user_pool_client" "dashboard" {
  name         = "${var.name}-dashboard"
  user_pool_id = aws_cognito_user_pool.this.id

  generate_secret = false # public SPA client -> PKCE, no secret

  allowed_oauth_flows                  = ["code"]
  allowed_oauth_flows_user_pool_client = true
  allowed_oauth_scopes                 = ["openid", "email", "profile"]
  supported_identity_providers         = ["COGNITO"]

  callback_urls = var.callback_urls
  logout_urls   = var.logout_urls

  explicit_auth_flows = [
    "ALLOW_REFRESH_TOKEN_AUTH",
    "ALLOW_USER_SRP_AUTH",
  ]

  prevent_user_existence_errors = "ENABLED"
  enable_token_revocation       = true

  access_token_validity  = 60 # minutes
  id_token_validity      = 60 # minutes
  refresh_token_validity = 30 # days
  token_validity_units {
    access_token  = "minutes"
    id_token      = "minutes"
    refresh_token = "days"
  }
}

# Seed the named admin users. Cognito emails each a temporary password.
resource "aws_cognito_user" "admins" {
  for_each     = toset(var.admin_emails)
  user_pool_id = aws_cognito_user_pool.this.id
  username     = each.value

  attributes = {
    email          = each.value
    email_verified = "true"
  }

  desired_delivery_mediums = ["EMAIL"]
}

resource "aws_cognito_user_group" "admins" {
  name         = "admins"
  user_pool_id = aws_cognito_user_pool.this.id
  description  = "Dashboard administrators."
}
