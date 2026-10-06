"""Guards for infra/account: applied by hand, never by CI, and nothing personal committed."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKFLOW = (ROOT / ".github/workflows/deploy.yml").read_text()
SSO = ROOT / "infra/account/sso.tf"


def env_value(name):
    match = re.search(rf"^  {name}: (.+)$", WORKFLOW, re.M)
    assert match, f"{name} is not set in deploy.yml"
    return match.group(1).split()


def test_account_stack_is_checked_but_never_deployed():
    assert "account" in env_value("CHECK_STACKS")
    assert "account" not in env_value("TF_STACKS")


def test_check_job_loops_over_check_stacks():
    assert "for stack in $CHECK_STACKS" in WORKFLOW


def test_administrator_resources_cannot_be_destroyed():
    text = SSO.read_text()
    blocks = re.findall(r'^resource "(aws_ssoadmin_[a-z_]+)" "administrator" \{\n(.*?)^\}', text, re.M | re.S)
    assert {b[0] for b in blocks} == {"aws_ssoadmin_permission_set", "aws_ssoadmin_managed_policy_attachment", "aws_ssoadmin_account_assignment"}
    for kind, body in blocks:
        assert re.search(r"prevent_destroy\s*=\s*true", body), kind


def test_personal_and_local_files_are_ignored():
    ignored = (ROOT / ".gitignore").read_text().splitlines()
    assert "infra/account/terraform.tfvars" in ignored
    assert "infra/account/imports.tf" in ignored


def test_state_loss_recovery_is_documented():
    readme = (ROOT / "infra/account/README.md").read_text()
    assert "never apply" in readme.lower()
    assert "import" in readme and "-target" in readme


def test_budget_recipient_is_shown_in_local_plans():
    # A valid-but-wrong address passes validation, so the plan must show who gets the alerts.
    outputs = (ROOT / "infra/account/outputs.tf").read_text()
    assert re.search(r'output "budget_alert_recipient"[^}]*value\s*=\s*var\.budget_email', outputs, re.S)
    assert "sensitive" not in outputs
