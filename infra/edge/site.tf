resource "aws_s3_bucket" "site" {
  bucket        = "davidkayode.com"
  force_destroy = false

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "site" {
  bucket                  = aws_s3_bucket.site.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_versioning" "site" {
  bucket = aws_s3_bucket.site.id

  versioning_configuration {
    status = "Enabled"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_policy" "site" {
  bucket = aws_s3_bucket.site.id
  policy = jsonencode({
    Id      = "PolicyForCloudFrontPrivateContent"
    Version = "2008-10-17"
    Statement = [{
      Sid       = "AllowCloudFrontServicePrincipal"
      Effect    = "Allow"
      Principal = { Service = "cloudfront.amazonaws.com" }
      Action    = "s3:GetObject"
      Resource  = "${aws_s3_bucket.site.arn}/*"
      Condition = {
        StringEquals = { "AWS:SourceArn" = aws_cloudfront_distribution.site.arn }
      }
    }]
  })

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_cloudfront_origin_access_control" "site" {
  description                       = ""
  name                              = "davidkayode.com.s3.us-east-1.amazonaws.com"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_acm_certificate" "site" {
  domain_name               = "davidkayode.com"
  subject_alternative_names = ["*.davidkayode.com", "davidkayode.com"]
  validation_method         = "DNS"
  key_algorithm             = "RSA_2048"

  options {
    certificate_transparency_logging_preference = "ENABLED"
  }

  lifecycle {
    prevent_destroy = true
  }
}

locals {
  s3_origin_id = "davidkayode.com.s3.us-east-1.amazonaws.com"
}

resource "aws_cloudfront_distribution" "site" {
  aliases             = ["davidkayode.com", "www.davidkayode.com"]
  default_root_object = "index.html"
  enabled             = true
  http_version        = "http2"
  is_ipv6_enabled     = true
  price_class         = "PriceClass_All"

  origin {
    domain_name              = aws_s3_bucket.site.bucket_regional_domain_name
    origin_id                = local.s3_origin_id
    origin_access_control_id = aws_cloudfront_origin_access_control.site.id
  }

  default_cache_behavior {
    target_origin_id       = local.s3_origin_id
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods        = ["GET", "HEAD"]
    cached_methods         = ["GET", "HEAD"]
    compress               = true
    cache_policy_id        = "658327ea-f89d-4fab-a63d-7e88639e58f6" # Managed-CachingOptimized
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.site.arn
    minimum_protocol_version = "TLSv1.2_2021"
    ssl_support_method       = "sni-only"
  }

  lifecycle {
    prevent_destroy = true
  }
}
