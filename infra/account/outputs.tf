# Printed by every local plan/apply so a mistyped (but valid) address is noticed.
# CI only runs mocked tests, so this never reaches public logs.
output "budget_alert_recipient" {
  description = "Address that receives both budget alerts."
  value       = var.budget_email
}
