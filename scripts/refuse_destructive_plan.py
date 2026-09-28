"""Exit non-zero if a Terraform JSON plan deletes, replaces or quietly disarms a protected resource."""
import json
import sys

PUBLIC_ACCESS_FLAGS = ("block_public_acls", "block_public_policy", "ignore_public_acls", "restrict_public_buckets")


def _first(value):
    return value[0] if isinstance(value, list) and value else {}


def _dropped_protection(before, after):
    return before is True and after is not True


# In-place updates that are as bad as a delete: each check gets (before, after).
DISARMING_UPDATES = {
    "aws_dynamodb_table": lambda b, a: _dropped_protection(b.get("deletion_protection_enabled"), a.get("deletion_protection_enabled")),
    "aws_s3_bucket_versioning": lambda b, a: _first(b.get("versioning_configuration")).get("status") == "Enabled"
    and _first(a.get("versioning_configuration")).get("status") != "Enabled",
    "aws_s3_bucket_public_access_block": lambda b, a: any(_dropped_protection(b.get(f), a.get(f)) for f in PUBLIC_ACCESS_FLAGS),
    "aws_cloudfront_distribution": lambda b, a: _dropped_protection(b.get("enabled"), a.get("enabled"))
    or bool(set(b.get("aliases") or []) - set(a.get("aliases") or [])),
    "aws_route53_record": lambda b, a: b.get("alias") != a.get("alias") or b.get("records") != a.get("records"),
}


def _is_destructive(change):
    actions = change.get("change", {}).get("actions", [])
    if "delete" in actions:
        return True
    check = DISARMING_UPDATES.get(change.get("type"))
    if "update" in actions and check:
        return check(change["change"].get("before") or {}, change["change"].get("after") or {})
    return False


def destructive_changes(plan):
    return sorted(change["address"] for change in plan.get("resource_changes", []) if _is_destructive(change))


def main(path):
    with open(path) as f:
        bad = destructive_changes(json.load(f))
    if bad:
        print("Refusing to apply a plan that deletes, replaces or disarms:", *bad, sep="\n  ")
        print("Re-run the Deploy workflow by hand with allow_destroy if this is intended.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
