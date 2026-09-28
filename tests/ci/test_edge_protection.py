"""Every resource in the edge stack is live, imported infrastructure: none may be destroyable."""
import pathlib
import re

EDGE = pathlib.Path(__file__).resolve().parents[2] / "infra/edge"


def resource_blocks():
    for tf in sorted(EDGE.glob("*.tf")):
        text = tf.read_text()
        for match in re.finditer(r'^resource "([^"]+)" "([^"]+)" \{\n(.*?)^\}', text, re.M | re.S):
            yield f"{match.group(1)}.{match.group(2)}", match.group(3)


def test_edge_has_resources():
    assert len(list(resource_blocks())) >= 11


def test_every_edge_resource_has_prevent_destroy():
    unprotected = [name for name, body in resource_blocks() if not re.search(r"prevent_destroy\s*=\s*true", body)]
    assert not unprotected, unprotected
