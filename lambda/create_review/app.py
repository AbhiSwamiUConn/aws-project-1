import boto3
import os
import uuid
from datetime import datetime, timezone
from decimal import Decimal

ddb = boto3.resource("dynamodb")
table = ddb.Table(os.environ["REVIEWS_TABLE"])

def to_dynamo_safe(value):
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: to_dynamo_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_dynamo_safe(v) for v in value]
    return value

def lambda_handler(event, context):
    task_token = event["task_token"]
    feedback = to_dynamo_safe(event["feedback"])

    review_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()

    item = {
        "review_id": review_id,
        "task_token": task_token,
        "status": "PENDING",
        "created_at": now,
        "feedback": feedback
    }

    table.put_item(Item=item)

    return {
        "review_id": review_id,
        "status": "PENDING",
        "feedback_id": feedback["feedback_id"]
    }
