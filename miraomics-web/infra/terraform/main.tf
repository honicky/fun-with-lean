locals {
  name      = "${var.project}-${var.environment}"
  site_fqdn = var.site_subdomain == "" ? var.domain_name : "${var.site_subdomain}.${var.domain_name}"
  site_url  = "https://${local.site_fqdn}"

  tags = merge({
    Project     = var.project
    Environment = var.environment
    ManagedBy   = "terraform"
  }, var.tags)
}

# Keyless CI/CD: role GitHub Actions assumes via OIDC (requirement #3).
module "github_oidc" {
  source           = "./modules/github-oidc"
  name             = local.name
  github_repo      = var.github_repo
  github_branch    = var.github_branch
  state_bucket     = "miraomics-tfstate"
  state_lock_table = "miraomics-tflock"
  tags             = local.tags
}

# Dashboard access control (requirements #6, #7).
module "auth" {
  source        = "./modules/auth"
  name          = local.name
  region        = var.aws_region
  domain_prefix = var.cognito_domain_prefix
  admin_emails  = var.admin_emails

  callback_urls = [
    "${local.site_url}/dashboard/callback",
    "http://localhost:4321/dashboard/callback",
  ]
  logout_urls = [
    "${local.site_url}/",
    "http://localhost:4321/",
  ]
  tags = local.tags
}

# Static site hosting (requirements #1, #2, #8 are served from here).
module "static_site" {
  source = "./modules/static-site"
  providers = {
    aws           = aws
    aws.us_east_1 = aws.us_east_1
  }
  name            = local.name
  domain_name     = var.domain_name
  site_subdomain  = var.site_subdomain
  route53_zone_id = var.route53_zone_id
  tags            = local.tags
}

# Forms + attribution + dashboard API (requirements #4, #5, #6).
module "app_api" {
  source                   = "./modules/app-api"
  name                     = local.name
  region                   = var.aws_region
  allowed_origin           = local.site_url
  notify_email             = var.notify_email
  ses_from_email           = var.ses_from_email
  verify_ses_from_identity = var.verify_ses_from_identity
  cognito_issuer           = module.auth.issuer
  cognito_client_id        = module.auth.client_id

  domain_name     = var.domain_name
  api_subdomain   = var.api_subdomain
  route53_zone_id = var.route53_zone_id
  tags            = local.tags
}
