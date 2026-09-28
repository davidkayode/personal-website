"""Exit non-zero if a Terraform JSON plan deletes or replaces any resource."""
import json
import sys


def destructive_changes(plan):
    return sorted(
        change["address"]
        for change in plan.get("resource_changes", [])
        if "delete" in change.get("change", {}).get("actions", [])
    )


def main(path):
    with open(path) as f:
        bad = destructive_changes(json.load(f))
    if bad:
        print("Refusing to apply a plan that deletes or replaces:", *bad, sep="\n  ")
        print("Re-run the Deploy workflow by hand with allow_destroy if this is intended.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1]))
