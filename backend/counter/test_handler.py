import importlib.util
import json
import os
import pathlib

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

# Keep boto3 offline: no metadata-endpoint lookups and no real credentials.
os.environ["AWS_DEFAULT_REGION"] = "us-east-1"
os.environ["AWS_EC2_METADATA_DISABLED"] = "true"
os.environ["AWS_ACCESS_KEY_ID"] = "testing"
os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
os.environ.pop("AWS_PROFILE", None)

TABLE = "test-visitors"


def load_handler():
    path = pathlib.Path(__file__).with_name("handler.py")
    spec = importlib.util.spec_from_file_location("counter_handler", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def dynamodb(monkeypatch):
    monkeypatch.setenv("TABLE_NAME", TABLE)
    with mock_aws():
        client = boto3.client("dynamodb")
        client.create_table(
            TableName=TABLE,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        yield client


def stored_count(client):
    item = client.get_item(TableName=TABLE, Key={"id": {"S": "0001"}}).get("Item")
    return int(item["visitorCounter"]["N"]) if item else None


def body(response):
    return json.loads(response["body"])


def test_first_visit_on_an_empty_table_counts_one(dynamodb):
    response = load_handler().lambda_handler({}, None)
    assert response["statusCode"] == 200
    assert body(response) == {"value": 1}
    assert stored_count(dynamodb) == 1


def test_seeded_count_carries_on(dynamodb):
    dynamodb.put_item(TableName=TABLE, Item={"id": {"S": "0001"}, "visitorCounter": {"N": "772"}})
    assert body(load_handler().lambda_handler({}, None)) == {"value": 773}
    assert stored_count(dynamodb) == 773


def test_each_call_adds_exactly_one(dynamodb):
    handler = load_handler()
    values = [body(handler.lambda_handler({}, None))["value"] for _ in range(3)]
    assert values == [1, 2, 3]


def test_response_is_json_with_an_integer(dynamodb):
    response = load_handler().lambda_handler({}, None)
    assert response["headers"] == {"Content-Type": "application/json"}
    assert isinstance(body(response)["value"], int)


class SpyTable:
    """Wraps the real table and records which DynamoDB calls the handler makes."""

    def __init__(self, table):
        self._table = table
        self.calls = []

    def __getattr__(self, name):
        self.calls.append(name)
        return getattr(self._table, name)


def test_increment_is_a_single_atomic_update(dynamodb):
    # A read-then-write handler loses visits when two requests overlap.
    handler = load_handler()
    spy = SpyTable(boto3.resource("dynamodb").Table(TABLE))
    handler._table = spy
    handler.lambda_handler({}, None)
    assert spy.calls == ["update_item"]


class FailingTable:
    def update_item(self, **kwargs):
        raise ClientError({"Error": {"Code": "ProvisionedThroughputExceededException", "Message": "slow down"}}, "UpdateItem")


def test_dynamodb_failure_returns_500_without_details(dynamodb):
    handler = load_handler()
    handler._table = FailingTable()
    response = handler.lambda_handler({}, None)
    assert response["statusCode"] == 500
    assert body(response) == {"error": "counter unavailable"}
