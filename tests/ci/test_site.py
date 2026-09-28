import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
HTML = (ROOT / "site/index.html").read_text()
JS = (ROOT / "site/script.js").read_text()


def test_page_needs_no_config_script_tag():
    # script.js fetches /config.json itself, so a cached index.html can't break the counter.
    assert "config.js" not in HTML
    assert '<script src="script.js"></script>' in HTML


def test_counter_script_has_no_hard_coded_api():
    assert "execute-api" not in JS
    assert "fetch('/config.json'" in JS


def test_generated_config_is_not_committed():
    lines = (ROOT / ".gitignore").read_text().splitlines()
    assert "site/config.json" in lines
