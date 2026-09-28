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
