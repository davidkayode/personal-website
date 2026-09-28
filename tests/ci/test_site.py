import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
HTML = (ROOT / "site/index.html").read_text()
JS = (ROOT / "site/script.js").read_text()


def test_config_loads_before_the_counter_script():
    assert HTML.index('<script src="config.js"></script>') < HTML.index('<script src="script.js"></script>')


def test_counter_script_has_no_hard_coded_api():
    assert "execute-api" not in JS
    assert "window.COUNTER_API_URL" in JS


def test_counter_script_skips_the_request_without_config():
    assert JS.index("if (!url)") < JS.index("fetch(")


def test_generated_config_is_not_committed():
    assert "site/config.js" in (ROOT / ".gitignore").read_text().splitlines()
