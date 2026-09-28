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


def test_dns_roles_are_limited_to_the_one_zone():
    for name in ("dns-policy.json", "dns-read-policy.json"):
        for s in allow_statements(render(name)):
            if any(a.startswith("route53:") and a not in ("route53:ListHostedZones", "route53:ListHostedZonesByName", "route53:GetChange") for a in actions(s)):
                assert s["Resource"] == "arn:aws:route53:::hostedzone/ZTEST", name


def test_read_role_cannot_change_records():
    granted = [a for s in allow_statements(render("dns-read-policy.json")) for a in actions(s)]
    assert not any(a.startswith("route53:Change") for a in granted)


def test_dns_trust_names_exact_principals():
    for name, expected in (("dns-trust.json", ":role/GitHub_Role"), ("dns-read-trust.json", ":role/GitHub_Plan_Role")):
        principals = render(name)["Statement"][0]["Condition"]["ArnLike"]["aws:PrincipalArn"]
        assert any(p.endswith(expected) for p in principals), name
        assert all(":role/" in p for p in principals), name


def test_role_policy_edits_require_the_boundary():
    # Editing an unbounded personal-website-* role would be an escalation path.
    doc = render("deploy.json")
    for s in allow_statements(doc):
        acts = actions(s)
        if any(a in acts for a in ("iam:PutRolePolicy", "iam:DeleteRolePolicy")):
            assert s.get("Condition", {}).get("StringEquals", {}).get("iam:PermissionsBoundary", "").endswith(":policy/personal-website-lambda-boundary"), s["Sid"]
        assert "iam:UpdateAssumeRolePolicy" not in acts, s["Sid"]


SITE_RECORDS = {"davidkayode.com", "www.davidkayode.com", "_39a51f8ff3602f772775bf91428fada0.davidkayode.com"}


def test_dns_role_can_only_change_the_site_records():
    changes = [s for s in allow_statements(render("dns-policy.json")) if "route53:ChangeResourceRecordSets" in actions(s)]
    assert changes
    for s in changes:
        names = s["Condition"]["ForAllValues:StringEquals"]["route53:ChangeResourceRecordSetsNormalizedRecordNames"]
        types = s["Condition"]["ForAllValues:StringEquals"]["route53:ChangeResourceRecordSetsRecordTypes"]
        assert set(names) == SITE_RECORDS
        assert set(types) == {"A", "CNAME"}


def test_deploy_role_has_no_wildcard_lambda_access():
    granted = [a for s in allow_statements(render("deploy.json")) for a in actions(s)]
    assert "lambda:*" not in granted
    assert not any("FunctionUrl" in a for a in granted)


def test_deploy_role_is_denied_public_function_urls():
    denies = [a for s in render("deploy.json")["Statement"] if s["Effect"] == "Deny" for a in actions(s)]
    assert {"lambda:CreateFunctionUrlConfig", "lambda:UpdateFunctionUrlConfig"} <= set(denies)
