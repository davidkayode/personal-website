# personal-website

Source for [davidkayode.com](https://davidkayode.com), a Cloud Resume Challenge build.

| Path | What |
|---|---|
| `site/` | Static site, deployed to S3 as-is |
| `backend/counter/` | Visitor counter Lambda (Python) |
| `infra/` | Terraform for the counter stack |
| `tests/e2e/` | Cypress smoke test against production |

Every push to `main` runs `.github/workflows/deploy.yml`. Pull requests run checks, and a Terraform plan when enabled.
