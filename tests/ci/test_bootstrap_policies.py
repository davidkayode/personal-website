import json
import pathlib
import re

POLICIES = pathlib.Path(__file__).resolve().parents[2] / "infra/bootstrap/policies"
FILL = {"@ACCOUNT_ID@": "111111111111", "@MGMT_ACCOUNT_ID@": "222222222222", "@STATE_BUCKET@": "state", "@ZONE_ID@": "ZTEST"}


def render(name):
    text = (POLICIES / name).read_text()
    for key, value in FILL.items():
        text = text.replace(key, value)
    return json.loads(text)


def actions(statement):
    value = statement.get("Action", [])
    return [value] if isinstance(value, str) else value


def allow_statements(doc):
    return [s for s in doc["Statement"] if s["Effect"] == "Allow"]


def test_templates_exist_and_render_to_json():
    names = {p.name for p in POLICIES.glob("*.json")}
    assert {"lambda-boundary.json", "deploy.json", "plan-trust.json"} <= names
    for name in names:
        render(name)


def test_templates_hold_no_real_account_ids():
    for path in POLICIES.glob("*.json"):
        assert not re.search(r"\b\d{12}\b", path.read_text()), path.name


def test_deploy_role_cannot_grant_itself_more():
    granted = [a for s in allow_statements(render("deploy.json")) for a in actions(s)]
    for forbidden in ("*", "iam:*", "iam:AttachRolePolicy", "iam:CreatePolicy", "iam:CreatePolicyVersion", "iam:DeleteRolePermissionsBoundary"):
        assert forbidden not in granted


def test_roles_the_deploy_role_creates_must_carry_the_boundary():
    doc = render("deploy.json")
    creates = [s for s in allow_statements(doc) if "iam:CreateRole" in actions(s)]
    assert creates, "deploy.json must allow iam:CreateRole"
    for s in creates:
        boundary = s["Condition"]["StringEquals"]["iam:PermissionsBoundary"]
        assert boundary.endswith(":policy/personal-website-lambda-boundary")


def test_pass_role_only_to_lambda():
    doc = render("deploy.json")
    passes = [s for s in allow_statements(doc) if "iam:PassRole" in actions(s)]
    assert passes
    for s in passes:
        assert s["Condition"]["StringEquals"]["iam:PassedToService"] == "lambda.amazonaws.com"


def test_boundary_limits_lambdas_to_the_counter_table_and_logs():
    granted = {a for s in allow_statements(render("lambda-boundary.json")) for a in actions(s)}
    assert granted <= {"dynamodb:UpdateItem", "dynamodb:GetItem", "logs:CreateLogStream", "logs:PutLogEvents"}


def test_plan_role_trusts_only_pull_requests():
    doc = render("plan-trust.json")
    subjects = doc["Statement"][0]["Condition"]["StringLike"]["token.actions.githubusercontent.com:sub"]
    assert subjects and all(s.endswith(":pull_request") for s in subjects)
