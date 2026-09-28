"""Guards on .github/workflows/deploy.yml that the linter can't express."""
import pathlib
import re

WORKFLOW = pathlib.Path(__file__).resolve().parents[2] / ".github/workflows/deploy.yml"


def top_level_block(text, key):
    match = re.search(rf"^{key}:\n((?:[ ]+.*\n)+)", text, re.M)
    return match.group(1) if match else ""


def job_block(text, job):
    match = re.search(rf"^  {job}:\n((?:(?:    .*)?\n)+?)(?=^  \S|\Z)", text, re.M)
    return match.group(1) if match else ""


def test_pr_runs_do_not_share_the_production_queue():
    # One shared group lets a newer PR run cancel a pending main deploy.
    workflow_concurrency = top_level_block(WORKFLOW.read_text(), "concurrency")
    assert "group: production" not in workflow_concurrency
    assert "github.ref" in workflow_concurrency


def test_deploy_job_is_serialised_and_never_cancelled():
    deploy = job_block(WORKFLOW.read_text(), "deploy")
    assert re.search(r"concurrency:\s*\n\s+group: production\s*\n\s+cancel-in-progress: false", deploy)


def test_smoke_still_runs_when_check_was_skipped():
    # Without a status function, a skipped `check` upstream skips smoke on site-only pushes.
    smoke = job_block(WORKFLOW.read_text(), "smoke")
    condition = re.search(r"^\s+if:\s*(.+)$", smoke, re.M).group(1)
    assert "!cancelled()" in condition
    assert "needs.deploy.result == 'success'" in condition


def test_deploy_writes_config_then_syncs_then_invalidates():
    deploy = job_block(WORKFLOW.read_text(), "deploy")
    assert deploy.index("site/config.js") < deploy.index("aws s3 sync site/") < deploy.index("create-invalidation")


def test_deploy_refuses_an_empty_api_url():
    assert 'test -n "$url"' in job_block(WORKFLOW.read_text(), "deploy")


def test_plan_job_uses_the_read_only_role():
    plan = job_block(WORKFLOW.read_text(), "plan")
    assert "secrets.AWS_PLAN_ROLE_ARN" in plan
    assert "secrets.AWS_ROLE_ARN" not in plan


def test_deploy_needs_a_successful_changes_job():
    assert "needs.changes.result == 'success'" in job_block(WORKFLOW.read_text(), "deploy")


def test_terraform_version_supports_native_state_locking():
    major, minor = map(int, re.search(r"TF_VERSION: (\d+)\.(\d+)", WORKFLOW.read_text()).groups())
    assert (major, minor) >= (1, 10)


def test_check_job_runs_terraform_tests_for_each_stack():
    assert 'terraform -chdir="infra/$stack" test' in job_block(WORKFLOW.read_text(), "check")


def test_destroying_resources_is_opt_in():
    text = WORKFLOW.read_text()
    assert "allow_destroy" in text
    assert "ALLOW_DESTROY" in job_block(text, "deploy")
