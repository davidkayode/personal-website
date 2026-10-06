"""The repo is public: the only email address allowed in it is the site's own contact address."""
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).resolve().parents[2]
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")
ALLOWED = {"davidkayode009@yahoo.com"}  # public contact link on the site
SKIP_SUFFIXES = (".png", ".jpg", ".ico", ".pdf")


def tracked_files():
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [f for f in out.split("\0") if f and not f.endswith(SKIP_SUFFIXES)]


def test_no_personal_email_addresses_in_tracked_files():
    hits = []
    for name in tracked_files():
        for address in EMAIL.findall((ROOT / name).read_text(errors="ignore")):
            if address not in ALLOWED and not address.endswith("@example.com"):
                hits.append(f"{name}: {address}")
    assert not hits, hits
