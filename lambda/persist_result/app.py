import boto3
import os
from datetime import datetime, timezone
from decimal import Decimal

ddb = boto3.resource("dynamodb")
table = ddb.Table(os.environ["RESULTS_TABLE"])

def to_dynamo_safe(value):
    if isinstance(value, float):
        return Decimal(str(value))
    if isinstance(value, dict):
        return {k: to_dynamo_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [to_dynamo_safe(v) for v in value]
    return value

def lambda_handler(event, context):
    now = datetime.now(timezone.utc).isoformat()

    item = {
        "feedback_id": event["feedback_id"],
        "sentiment": event["sentiment"],
        "confidence": event["confidence"],
        "draft_response": event["draft_response"],
        "final_status": event["final_status"],
        "review_id": event.get("review_id"),
        "updated_at": now
    }

    table.put_item(Item=to_dynamo_safe(item))

    return {
        "ok": True,
        "feedback_id": event["feedback_id"]
    }
