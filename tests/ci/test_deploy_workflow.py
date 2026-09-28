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
    assert deploy.index("site/config.json") < deploy.index("aws s3 sync site/") < deploy.index("create-invalidation")


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


def test_edge_stack_is_part_of_every_run():
    assert re.search(r"TF_STACKS: counter edge\b", WORKFLOW.read_text())


def test_invalidation_uses_the_edge_output():
    deploy = job_block(WORKFLOW.read_text(), "deploy")
    assert "terraform -chdir=infra/edge output -raw distribution_id" in deploy
    assert "vars.CLOUDFRONT_DISTRIBUTION_ID" not in deploy


def test_each_job_reaches_dns_with_its_own_role():
    text = WORKFLOW.read_text()
    assert "TF_VAR_dns_role_arn: ${{ secrets.DNS_ROLE_ARN }}" in job_block(text, "deploy")
    assert "TF_VAR_dns_role_arn: ${{ secrets.DNS_READ_ROLE_ARN }}" in job_block(text, "plan")


def test_account_id_is_masked_in_every_aws_job():
    text = WORKFLOW.read_text()
    for job in ("plan", "deploy"):
        assert "::add-mask::" in job_block(text, job), job


def test_plan_comment_redacts_account_ids():
    assert r"\b\d{12}\b" in job_block(WORKFLOW.read_text(), "plan")


def test_site_files_are_uploaded_with_no_cache():
    deploy = job_block(WORKFLOW.read_text(), "deploy")
    assert '--cache-control "no-cache"' in deploy
    assert deploy.index("site/config.json") < deploy.index('--cache-control "no-cache"') < deploy.index("create-invalidation")


def test_check_job_runs_the_browser_script_tests():
    assert "node --test tests/js" in job_block(WORKFLOW.read_text(), "check")


def test_script_changes_trigger_the_checks():
    changes = job_block(WORKFLOW.read_text(), "changes")
    assert "'site/script.js'" in changes and "'tests/js/**'" in changes
