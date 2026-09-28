mock_provider "aws" {}

mock_provider "aws" {
  alias = "dns"
}

variables {
  dns_role_arn = "arn:aws:iam::123456789012:role/test-dns"
}

run "edge_config" {
  command = plan

  assert {
    condition     = toset(aws_cloudfront_distribution.site.aliases) == toset(["davidkayode.com", "www.davidkayode.com"])
    error_message = "CloudFront must answer for the apex and www."
  }
  assert {
    condition     = aws_cloudfront_distribution.site.default_root_object == "index.html"
    error_message = "The default root object must be index.html."
  }
  assert {
    condition     = aws_cloudfront_distribution.site.default_cache_behavior[0].viewer_protocol_policy == "redirect-to-https"
    error_message = "Viewers must be redirected to HTTPS."
  }
  assert {
    condition     = aws_s3_bucket.site.bucket == "davidkayode.com"
    error_message = "The site bucket must be davidkayode.com."
  }
  assert {
    condition     = aws_s3_bucket_public_access_block.site.block_public_acls && aws_s3_bucket_public_access_block.site.block_public_policy && aws_s3_bucket_public_access_block.site.ignore_public_acls && aws_s3_bucket_public_access_block.site.restrict_public_buckets
    error_message = "The site bucket must block all public access."
  }
  assert {
    condition     = aws_s3_bucket_versioning.site.versioning_configuration[0].status == "Enabled"
    error_message = "Site bucket versioning must stay on."
  }
  assert {
    condition     = aws_route53_zone.main.name == "davidkayode.com"
    error_message = "The zone must be davidkayode.com."
  }
  assert {
    condition     = aws_route53_record.apex.type == "A" && length(aws_route53_record.apex.alias) == 1
    error_message = "The apex must be an alias A record."
  }
}
