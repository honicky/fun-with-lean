output "api_base_url" {
  description = "Base URL the frontend calls (PUBLIC_API_BASE_URL)."
  value       = local.enable_api_dns ? "https://${local.api_fqdn}" : aws_apigatewayv2_api.this.api_endpoint
}

output "api_endpoint" {
  description = "Raw API Gateway endpoint (no custom domain)."
  value       = aws_apigatewayv2_api.this.api_endpoint
}

output "table_name" {
  value = aws_dynamodb_table.events.name
}

output "lambda_function_names" {
  description = "For CI code updates."
  value = {
    submit    = aws_lambda_function.submit.function_name
    track     = aws_lambda_function.track.function_name
    dashboard = aws_lambda_function.dashboard.function_name
  }
}
