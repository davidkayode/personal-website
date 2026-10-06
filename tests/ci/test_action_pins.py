"""Third-party code must be pinned: actions to a commit SHA, and no scripts from other sites."""
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKFLOWS = sorted((ROOT / ".github/workflows").glob("*.yml"))


def uses_lines():
    for wf in WORKFLOWS:
        for line in wf.read_text().splitlines():
            if re.match(r"\s*-?\s*uses:", line):
                yield wf.name, line.strip()


def test_every_action_is_pinned_to_a_commit_sha_with_its_version():
    lines = list(uses_lines())
    assert lines
    bad = [f"{wf}: {line}" for wf, line in lines if not re.search(r"uses: [\w.-]+/[\w.-]+@[0-9a-f]{40} # v\d+\.\d+\.\d+$", line)]
    assert not bad, bad


def test_dependabot_keeps_the_pins_current():
    config = (ROOT / ".github/dependabot.yml").read_text()
    assert 'package-ecosystem: "github-actions"' in config
    assert "interval:" in config


def test_site_loads_no_scripts_from_other_sites():
    html = (ROOT / "site/index.html").read_text()
    assert not re.search(r'<script[^>]+src="https?://', html)
    assert "ion-icon" not in html
