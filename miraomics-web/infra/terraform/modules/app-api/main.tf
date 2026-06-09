data "aws_caller_identity" "current" {}

locals {
  lambda_root    = "${path.module}/../../../lambda"
  enable_email   = var.notify_email != "" && var.ses_from_email != ""
  enable_api_dns = var.route53_zone_id != "" && var.api_subdomain != "" && var.domain_name != ""
  api_fqdn       = "${var.api_subdomain}.${var.domain_name}"
}

# --- Storage: single events table (leads + pageviews) ------------------------
resource "aws_dynamodb_table" "events" {
  name         = "${var.name}-events"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "pk"
  range_key    = "sk"

  attribute {
    name = "pk"
    type = "S"
  }
  attribute {
    name = "sk"
    type = "S"
  }

  ttl {
    attribute_name = "ttl"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = true
  }
  server_side_encryption {
    enabled = true
  }

  tags = var.tags
}

# --- Optional SES sender identity --------------------------------------------
resource "aws_ses_email_identity" "from" {
  count = local.enable_email && var.verify_ses_from_identity ? 1 : 0
  email = var.ses_from_email
}

# --- Shared CloudWatch Logs policy -------------------------------------------
data "aws_iam_policy_document" "assume_lambda" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

# --- Lambda packaging ---------------------------------------------------------
data "archive_file" "submit" {
  type        = "zip"
  source_dir  = "${local.lambda_root}/submit-form"
  output_path = "${path.module}/.build/submit-form.zip"
}
data "archive_file" "track" {
  type        = "zip"
  source_dir  = "${local.lambda_root}/track"
  output_path = "${path.module}/.build/track.zip"
}
data "archive_file" "dashboard" {
  type        = "zip"
  source_dir  = "${local.lambda_root}/dashboard-api"
  output_path = "${path.module}/.build/dashboard-api.zip"
}

# --- submit-form (writer + SES) ----------------------------------------------
resource "aws_iam_role" "submit" {
  name               = "${var.name}-submit"
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
  tags               = var.tags
}

data "aws_iam_policy_document" "submit" {
  statement {
    actions   = ["dynamodb:PutItem"]
    resources = [aws_dynamodb_table.events.arn]
  }
  dynamic "statement" {
    for_each = local.enable_email ? [1] : []
    content {
      actions   = ["ses:SendEmail", "ses:SendRawEmail"]
      resources = ["arn:aws:ses:${var.region}:${data.aws_caller_identity.current.account_id}:identity/*"]
    }
  }
  statement {
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
}
resource "aws_iam_role_policy" "submit" {
  name   = "submit"
  role   = aws_iam_role.submit.id
  policy = data.aws_iam_policy_document.submit.json
}

resource "aws_lambda_function" "submit" {
  function_name    = "${var.name}-submit"
  role             = aws_iam_role.submit.arn
  runtime          = "nodejs20.x"
  handler          = "index.handler"
  filename         = data.archive_file.submit.output_path
  source_code_hash = data.archive_file.submit.output_base64sha256
  timeout          = 10
  memory_size      = 256

  environment {
    variables = {
      TABLE_NAME     = aws_dynamodb_table.events.name
      NOTIFY_EMAIL   = var.notify_email
      SES_FROM       = var.ses_from_email
      ALLOWED_ORIGIN = var.allowed_origin
    }
  }
  tags = var.tags
}

# --- track (writer) -----------------------------------------------------------
resource "aws_iam_role" "track" {
  name               = "${var.name}-track"
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
  tags               = var.tags
}
data "aws_iam_policy_document" "track" {
  statement {
    actions   = ["dynamodb:PutItem"]
    resources = [aws_dynamodb_table.events.arn]
  }
  statement {
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
}
resource "aws_iam_role_policy" "track" {
  name   = "track"
  role   = aws_iam_role.track.id
  policy = data.aws_iam_policy_document.track.json
}
resource "aws_lambda_function" "track" {
  function_name    = "${var.name}-track"
  role             = aws_iam_role.track.arn
  runtime          = "nodejs20.x"
  handler          = "index.handler"
  filename         = data.archive_file.track.output_path
  source_code_hash = data.archive_file.track.output_base64sha256
  timeout          = 5
  memory_size      = 128

  environment {
    variables = {
      TABLE_NAME     = aws_dynamodb_table.events.name
      PV_TTL_DAYS    = tostring(var.pageview_ttl_days)
      ALLOWED_ORIGIN = var.allowed_origin
    }
  }
  tags = var.tags
}

# --- dashboard-api (reader) ---------------------------------------------------
resource "aws_iam_role" "dashboard" {
  name               = "${var.name}-dashboard"
  assume_role_policy = data.aws_iam_policy_document.assume_lambda.json
  tags               = var.tags
}
data "aws_iam_policy_document" "dashboard" {
  statement {
    actions   = ["dynamodb:Query"]
    resources = [aws_dynamodb_table.events.arn, "${aws_dynamodb_table.events.arn}/index/*"]
  }
  statement {
    actions   = ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"]
    resources = ["arn:aws:logs:*:*:*"]
  }
}
resource "aws_iam_role_policy" "dashboard" {
  name   = "dashboard"
  role   = aws_iam_role.dashboard.id
  policy = data.aws_iam_policy_document.dashboard.json
}
resource "aws_lambda_function" "dashboard" {
  function_name    = "${var.name}-dashboard"
  role             = aws_iam_role.dashboard.arn
  runtime          = "nodejs20.x"
  handler          = "index.handler"
  filename         = data.archive_file.dashboard.output_path
  source_code_hash = data.archive_file.dashboard.output_base64sha256
  timeout          = 15
  memory_size      = 256

  environment {
    variables = {
      TABLE_NAME     = aws_dynamodb_table.events.name
      ALLOWED_ORIGIN = var.allowed_origin
    }
  }
  tags = var.tags
}

# --- HTTP API ----------------------------------------------------------------
resource "aws_apigatewayv2_api" "this" {
  name          = "${var.name}-api"
  protocol_type = "HTTP"

  cors_configuration {
    allow_origins  = [var.allowed_origin]
    allow_methods  = ["GET", "POST", "OPTIONS"]
    allow_headers  = ["content-type", "authorization"]
    expose_headers = ["content-type"]
    max_age        = 3600
  }
  tags = var.tags
}

# Cognito JWT authorizer for the /admin routes.
resource "aws_apigatewayv2_authorizer" "cognito" {
  api_id           = aws_apigatewayv2_api.this.id
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]
  name             = "${var.name}-cognito"

  jwt_configuration {
    issuer   = var.cognito_issuer
    audience = [var.cognito_client_id]
  }
}

locals {
  integrations = {
    submit    = aws_lambda_function.submit.invoke_arn
    track     = aws_lambda_function.track.invoke_arn
    dashboard = aws_lambda_function.dashboard.invoke_arn
  }
}

resource "aws_apigatewayv2_integration" "lambda" {
  for_each               = local.integrations
  api_id                 = aws_apigatewayv2_api.this.id
  integration_type       = "AWS_PROXY"
  integration_uri        = each.value
  payload_format_version = "2.0"
}

# Public routes
resource "aws_apigatewayv2_route" "submit" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "POST /submit"
  target    = "integrations/${aws_apigatewayv2_integration.lambda["submit"].id}"
}
resource "aws_apigatewayv2_route" "track" {
  api_id    = aws_apigatewayv2_api.this.id
  route_key = "POST /track"
  target    = "integrations/${aws_apigatewayv2_integration.lambda["track"].id}"
}

# Authorized dashboard routes
resource "aws_apigatewayv2_route" "admin_summary" {
  api_id             = aws_apigatewayv2_api.this.id
  route_key          = "GET /admin/summary"
  target             = "integrations/${aws_apigatewayv2_integration.lambda["dashboard"].id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}
resource "aws_apigatewayv2_route" "admin_leads" {
  api_id             = aws_apigatewayv2_api.this.id
  route_key          = "GET /admin/leads"
  target             = "integrations/${aws_apigatewayv2_integration.lambda["dashboard"].id}"
  authorization_type = "JWT"
  authorizer_id      = aws_apigatewayv2_authorizer.cognito.id
}

resource "aws_cloudwatch_log_group" "api" {
  name              = "/aws/apigw/${var.name}-api"
  retention_in_days = 90
  tags              = var.tags
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.this.id
  name        = "$default"
  auto_deploy = true

  access_log_settings {
    destination_arn = aws_cloudwatch_log_group.api.arn
    format = jsonencode({
      requestId  = "$context.requestId"
      ip         = "$context.identity.sourceIp"
      method     = "$context.httpMethod"
      route      = "$context.routeKey"
      status     = "$context.status"
      protocol   = "$context.protocol"
      latency    = "$context.responseLatency"
      authStatus = "$context.authorizer.error"
    })
  }

  default_route_settings {
    throttling_burst_limit = 50
    throttling_rate_limit  = 25
  }
  tags = var.tags
}

# Allow API Gateway to invoke each function.
resource "aws_lambda_permission" "apigw" {
  for_each      = local.integrations
  statement_id  = "AllowAPIGW-${each.key}"
  action        = "lambda:InvokeFunction"
  principal     = "apigateway.amazonaws.com"
  function_name = each.key == "submit" ? aws_lambda_function.submit.function_name : (each.key == "track" ? aws_lambda_function.track.function_name : aws_lambda_function.dashboard.function_name)
  source_arn    = "${aws_apigatewayv2_api.this.execution_arn}/*/*"
}

# --- Optional custom domain for the API (regional ACM cert) ------------------
resource "aws_acm_certificate" "api" {
  count             = local.enable_api_dns ? 1 : 0
  domain_name       = local.api_fqdn
  validation_method = "DNS"
  lifecycle {
    create_before_destroy = true
  }
  tags = var.tags
}

resource "aws_route53_record" "api_cert_validation" {
  for_each = local.enable_api_dns ? {
    for dvo in aws_acm_certificate.api[0].domain_validation_options : dvo.domain_name => {
      name   = dvo.resource_record_name
      type   = dvo.resource_record_type
      record = dvo.resource_record_value
    }
  } : {}
  zone_id         = var.route53_zone_id
  name            = each.value.name
  type            = each.value.type
  records         = [each.value.record]
  ttl             = 60
  allow_overwrite = true
}

resource "aws_acm_certificate_validation" "api" {
  count                   = local.enable_api_dns ? 1 : 0
  certificate_arn         = aws_acm_certificate.api[0].arn
  validation_record_fqdns = [for r in aws_route53_record.api_cert_validation : r.fqdn]
}

resource "aws_apigatewayv2_domain_name" "api" {
  count       = local.enable_api_dns ? 1 : 0
  domain_name = local.api_fqdn
  domain_name_configuration {
    certificate_arn = aws_acm_certificate_validation.api[0].certificate_arn
    endpoint_type   = "REGIONAL"
    security_policy = "TLS_1_2"
  }
  tags = var.tags
}

resource "aws_apigatewayv2_api_mapping" "api" {
  count       = local.enable_api_dns ? 1 : 0
  api_id      = aws_apigatewayv2_api.this.id
  domain_name = aws_apigatewayv2_domain_name.api[0].id
  stage       = aws_apigatewayv2_stage.default.id
}

resource "aws_route53_record" "api_alias" {
  count   = local.enable_api_dns ? 1 : 0
  zone_id = var.route53_zone_id
  name    = local.api_fqdn
  type    = "A"
  alias {
    name                   = aws_apigatewayv2_domain_name.api[0].domain_name_configuration[0].target_domain_name
    zone_id                = aws_apigatewayv2_domain_name.api[0].domain_name_configuration[0].hosted_zone_id
    evaluate_target_health = false
  }
}
