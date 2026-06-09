output "role_arn" {
  description = "Role ARN for the GitHub Actions aws-actions/configure-aws-credentials step."
  value       = aws_iam_role.deploy.arn
}
