# Bootstrap

These pieces can't be created by the pipeline that depends on them, so they're applied by hand with an admin SSO profile. Policy templates use `@ACCOUNT_ID@`-style placeholders so that no account ID is committed.

| Script | Profile | Creates |
|---|---|---|
| `state-bucket.sh` | `prod-admin` | Terraform state bucket (versioned, private, TLS-only) |
| `iam.sh` | `prod-admin` | `personal-website-lambda-boundary`, `personal-website-deploy` on `GitHub_Role`, `GitHub_Plan_Role` |
| `dns-roles.sh` | `admin` + `prod-admin` | `personal-website-dns` and `personal-website-dns-read` in the management account (stage 4) |

Re-running a script is safe. It updates what already exists.
