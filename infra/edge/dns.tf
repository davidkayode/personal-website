resource "aws_route53_zone" "main" {
  provider = aws.dns
  name     = "davidkayode.com"
  comment  = "HostedZone created by Route53 Registrar"

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_route53_record" "apex" {
  provider = aws.dns
  zone_id  = aws_route53_zone.main.zone_id
  name     = "davidkayode.com"
  type     = "A"

  alias {
    name                   = aws_cloudfront_distribution.site.domain_name
    zone_id                = aws_cloudfront_distribution.site.hosted_zone_id
    evaluate_target_health = false
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_route53_record" "www" {
  provider = aws.dns
  zone_id  = aws_route53_zone.main.zone_id
  name     = "www.davidkayode.com"
  type     = "CNAME"
  ttl      = 300
  records  = ["davidkayode.com"]

  lifecycle {
    prevent_destroy = true
  }
}

locals {
  # Certificate domains that have a DNS validation record. The apex and the
  # wildcard share one record, so only the apex is listed. Static keys keep
  # for_each known at plan time.
  cert_domains = toset(["davidkayode.com"])

  cert_validation = { for o in aws_acm_certificate.site.domain_validation_options : o.domain_name => o }
}

resource "aws_route53_record" "cert_validation" {
  provider = aws.dns
  for_each = local.cert_domains

  zone_id         = aws_route53_zone.main.zone_id
  name            = local.cert_validation[each.key].resource_record_name
  type            = local.cert_validation[each.key].resource_record_type
  ttl             = 300
  records         = [local.cert_validation[each.key].resource_record_value]
  allow_overwrite = false

  lifecycle {
    prevent_destroy = true
  }
}
