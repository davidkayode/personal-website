output "api_url" {
  description = "URL the site POSTs to for each visit."
  value       = "${aws_apigatewayv2_stage.prod.invoke_url}/count"
}
