# --- Consumed by CI to deploy the site ---------------------------------------
output "site_bucket" {
  description = "S3 bucket CI syncs the built site to."
  value       = module.static_site.bucket_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution CI invalidates after deploy."
  value       = module.static_site.distribution_id
}

output "lambda_function_names" {
  value = module.app_api.lambda_function_names
}

output "github_actions_role_arn" {
  description = "Set as AWS_DEPLOY_ROLE_ARN in GitHub repo variables."
  value       = module.github_oidc.role_arn
}

# --- Consumed at build time as PUBLIC_* env (frontend config) -----------------
output "site_url" {
  value = module.static_site.site_url
}

output "public_api_base_url" {
  description = "PUBLIC_API_BASE_URL"
  value       = module.app_api.api_base_url
}

output "public_cognito_domain" {
  description = "PUBLIC_COGNITO_DOMAIN"
  value       = module.auth.hosted_ui_domain
}

output "public_cognito_client_id" {
  description = "PUBLIC_COGNITO_CLIENT_ID"
  value       = module.auth.client_id
}

output "public_cognito_region" {
  description = "PUBLIC_COGNITO_REGION"
  value       = var.aws_region
}

output "public_dashboard_redirect_uri" {
  description = "PUBLIC_DASHBOARD_REDIRECT_URI"
  value       = "${module.static_site.site_url}/dashboard/callback"
}

# --- Operational -------------------------------------------------------------
output "dynamodb_table" {
  value = module.app_api.table_name
}

output "cognito_user_pool_id" {
  value = module.auth.user_pool_id
}
