"""The smoke test runs on every deploy, so it must never add a real visit."""
import pathlib
import re

SPEC = (pathlib.Path(__file__).resolve().parents[2] / "tests/e2e/cypress/e2e/spec.cy.js").read_text()


def test_page_visits_stub_the_counter_post():
    assert re.search(r"cy\.intercept\(\s*'POST'", SPEC)
    assert SPEC.index("cy.intercept(") < SPEC.index("cy.visit(")


def test_smoke_never_posts_to_the_api_itself():
    assert "method: 'POST'" not in SPEC


def test_live_api_is_checked_through_health():
    assert "/health" in SPEC


def test_live_cors_is_checked_for_each_host_with_a_preflight():
    # The page POST is stubbed, so a CORS preflight is what proves real visitors can still call the API.
    assert "method: 'OPTIONS'" in SPEC
    assert "'Access-Control-Request-Method': 'POST'" in SPEC
    assert "access-control-allow-origin" in SPEC
