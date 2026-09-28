import importlib.util
import json
import os
import pathlib
from decimal import Decimal

import pytest

# Keep boto3 offline: no metadata-endpoint lookups and no real credentials.
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_EC2_METADATA_DISABLED"] = "true"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ.pop("AWS_PROFILE", None)


def load_handler_module():
    # "lambda" is a Python keyword, so the handler module is loaded by path.
    path = pathlib.Path(__file__).with_name("lambda.py")
    spec = importlib.util.spec_from_file_location("counter_lambda", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeTable:
    def __init__(self, item=None):
        self.item = item
        self.puts = []
        self.updates = []

    def get_item(self, Key):
        return {"Item": self.item} if self.item is not None else {}

    def put_item(self, Item):
        self.puts.append(Item)
        self.item = Item

    def update_item(self, Key, UpdateExpression, ExpressionAttributeValues):
        self.updates.append((Key, UpdateExpression, ExpressionAttributeValues))
        self.item = {**self.item, "visitorCounter": ExpressionAttributeValues[":val1"]}


@pytest.fixture
def handler_module():
    return load_handler_module()


def test_first_visit_creates_item_and_returns_one(handler_module):
    handler_module.table = FakeTable(item=None)
    response = handler_module.lambda_handler({}, None)
    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"value": 1}
    assert handler_module.table.puts == [{"id": "0001", "visitorCounter": 1}]


def test_existing_count_is_incremented(handler_module):
    handler_module.table = FakeTable(item={"id": "0001", "visitorCounter": 41})
    response = handler_module.lambda_handler({}, None)
    assert response["statusCode"] == 200
    assert json.loads(response["body"]) == {"value": 42}
    assert handler_module.table.item["visitorCounter"] == 42


def test_body_is_json_with_integer_value(handler_module):
    # DynamoDB returns numbers as Decimal; the response must still be a JSON int.
    handler_module.table = FakeTable(item={"id": "0001", "visitorCounter": Decimal(9)})
    body = json.loads(handler_module.lambda_handler({}, None)["body"])
    assert body["value"] == 10 and isinstance(body["value"], int)
