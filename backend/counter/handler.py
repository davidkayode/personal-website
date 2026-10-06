import json
import logging
import os

import boto3
from botocore.exceptions import ClientError

COUNTER_ID = "0001"

logger = logging.getLogger()
logger.setLevel(logging.INFO)

_table = None


def table():
    global _table
    if _table is None:
        _table = boto3.resource("dynamodb").Table(os.environ["TABLE_NAME"])
    return _table


def _response(status, payload):
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def health():
    # Read-only: lets monitoring check the API and table without counting a visit.
    try:
        item = table().get_item(Key={"id": COUNTER_ID}).get("Item", {})
    except ClientError:
        logger.exception("Health check failed")
        return _response(503, {"status": "unavailable"})
    return _response(200, {"status": "ok", "value": int(item.get("visitorCounter", 0))})


def lambda_handler(event, context):
    if event.get("routeKey") == "GET /health":
        return health()
    try:
        result = table().update_item(
            Key={"id": COUNTER_ID},
            UpdateExpression="ADD visitorCounter :one",
            ExpressionAttributeValues={":one": 1},
            ReturnValues="UPDATED_NEW",
        )
    except ClientError:
        logger.exception("Counter update failed")
        return _response(500, {"error": "counter unavailable"})
    return _response(200, {"value": int(result["Attributes"]["visitorCounter"])})
