output "bucket_name" {
  description = "S3 bucket that holds the built site (CI syncs here)."
  value       = aws_s3_bucket.site.bucket
}

output "distribution_id" {
  description = "CloudFront distribution ID (CI invalidates this)."
  value       = aws_cloudfront_distribution.this.id
}

output "distribution_domain" {
  description = "CloudFront domain name."
  value       = aws_cloudfront_distribution.this.domain_name
}

output "site_url" {
  description = "Canonical public site URL."
  value       = local.enable_dns ? "https://${local.site_fqdn}" : "https://${aws_cloudfront_distribution.this.domain_name}"
}
