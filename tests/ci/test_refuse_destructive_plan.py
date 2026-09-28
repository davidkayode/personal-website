import importlib.util
import json
import pathlib

SCRIPT = pathlib.Path(__file__).resolve().parents[2] / "scripts/refuse_destructive_plan.py"


def load():
    spec = importlib.util.spec_from_file_location("refuse", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def plan(*changes):
    return {"resource_changes": [{"address": a, "change": {"actions": acts}} for a, acts in changes]}


def write(tmp_path, doc):
    path = tmp_path / "tfplan.json"
    path.write_text(json.dumps(doc))
    return str(path)


def test_creates_updates_and_imports_are_allowed(tmp_path):
    doc = plan(("aws_lambda_function.counter", ["create"]), ("aws_s3_bucket.site", ["update"]), ("aws_route53_zone.main", ["no-op"]))
    assert load().main(write(tmp_path, doc)) == 0


def test_a_delete_is_refused(tmp_path):
    assert load().main(write(tmp_path, plan(("aws_dynamodb_table.visitors", ["delete"])))) == 1


def test_a_replacement_is_refused(tmp_path):
    doc = plan(("aws_cloudfront_distribution.site", ["delete", "create"]), ("aws_acm_certificate.site", ["create", "delete"]))
    assert load().destructive_changes(doc) == ["aws_acm_certificate.site", "aws_cloudfront_distribution.site"]


def test_an_empty_plan_is_allowed(tmp_path):
    assert load().main(write(tmp_path, {})) == 0
