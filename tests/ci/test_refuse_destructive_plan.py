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


def update(address, rtype, before, after):
    return {"address": address, "type": rtype, "change": {"actions": ["update"], "before": before, "after": after}}


def test_turning_off_table_deletion_protection_is_refused():
    doc = {"resource_changes": [update("aws_dynamodb_table.visitors", "aws_dynamodb_table", {"deletion_protection_enabled": True}, {"deletion_protection_enabled": False})]}
    assert load().destructive_changes(doc) == ["aws_dynamodb_table.visitors"]


def test_suspending_bucket_versioning_is_refused():
    doc = {"resource_changes": [update("aws_s3_bucket_versioning.site", "aws_s3_bucket_versioning", {"versioning_configuration": [{"status": "Enabled"}]}, {"versioning_configuration": [{"status": "Suspended"}]})]}
    assert load().destructive_changes(doc) == ["aws_s3_bucket_versioning.site"]


def test_opening_public_access_is_refused():
    before = {"block_public_acls": True, "block_public_policy": True, "ignore_public_acls": True, "restrict_public_buckets": True}
    doc = {"resource_changes": [update("aws_s3_bucket_public_access_block.site", "aws_s3_bucket_public_access_block", before, {**before, "block_public_policy": False})]}
    assert load().destructive_changes(doc) == ["aws_s3_bucket_public_access_block.site"]


def test_disabling_cloudfront_or_dropping_an_alias_is_refused():
    before = {"enabled": True, "aliases": ["davidkayode.com", "www.davidkayode.com"]}
    doc = {"resource_changes": [
        update("aws_cloudfront_distribution.a", "aws_cloudfront_distribution", before, {**before, "enabled": False}),
        update("aws_cloudfront_distribution.b", "aws_cloudfront_distribution", before, {**before, "aliases": ["davidkayode.com"]}),
    ]}
    assert load().destructive_changes(doc) == ["aws_cloudfront_distribution.a", "aws_cloudfront_distribution.b"]


def test_retargeting_a_dns_record_is_refused():
    before = {"alias": [{"name": "d1.cloudfront.net", "zone_id": "Z2"}], "records": None}
    doc = {"resource_changes": [update("aws_route53_record.apex", "aws_route53_record", before, {**before, "alias": [{"name": "evil.example", "zone_id": "Z2"}]})]}
    assert load().destructive_changes(doc) == ["aws_route53_record.apex"]


def test_harmless_updates_still_pass(tmp_path):
    doc = {"resource_changes": [
        update("aws_lambda_function.counter", "aws_lambda_function", {"memory_size": 128}, {"memory_size": 256}),
        update("aws_cloudfront_distribution.site", "aws_cloudfront_distribution", {"enabled": True, "aliases": ["a"], "comment": None}, {"enabled": True, "aliases": ["a"], "comment": "x"}),
        update("aws_route53_record.www", "aws_route53_record", {"ttl": 300, "records": ["davidkayode.com"]}, {"ttl": 60, "records": ["davidkayode.com"]}),
    ]}
    assert load().main(write(tmp_path, doc)) == 0


def test_any_change_to_the_administrator_permission_set_is_refused():
    before = {"name": "Administrator", "session_duration": "PT1H", "description": "x"}
    doc = {"resource_changes": [update("aws_ssoadmin_permission_set.administrator", "aws_ssoadmin_permission_set", before, {**before, "session_duration": "PT12H"})]}
    assert load().destructive_changes(doc) == ["aws_ssoadmin_permission_set.administrator"]


def test_other_permission_sets_can_change():
    before = {"name": "Developer", "session_duration": "PT12H"}
    doc = {"resource_changes": [update("aws_ssoadmin_permission_set.developer", "aws_ssoadmin_permission_set", before, {**before, "session_duration": "PT8H"})]}
    assert load().destructive_changes(doc) == []
