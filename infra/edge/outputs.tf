output "distribution_id" {
  description = "CloudFront distribution to invalidate after each site sync."
  value       = aws_cloudfront_distribution.site.id
}
