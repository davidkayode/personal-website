"""David keeps AWS account IDs out of this public repo."""
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
PLACEHOLDERS = {"123456789012"}
SKIP_SUFFIXES = (".png", ".jpg", ".ico", ".pdf")
SKIP_FILES = {"tests/e2e/package-lock.json", "infra/counter/.terraform.lock.hcl", "infra/edge/.terraform.lock.hcl", "infra/account/.terraform.lock.hcl"}


def tracked_files():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [f for f in out.split("\0") if f and not f.endswith(SKIP_SUFFIXES) and f not in SKIP_FILES]


def test_no_aws_account_ids_in_tracked_files():
    hits = []
    for name in tracked_files():
        text = (ROOT / name).read_text(errors="ignore")
        for match in re.findall(r"(?<![\w.-])\d{12}(?![\w.-])", text):
            if len(set(match)) > 1 and match not in PLACEHOLDERS:
                hits.append(f"{name}: {match}")
    assert not hits, hits
