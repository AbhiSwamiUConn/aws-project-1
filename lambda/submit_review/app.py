import boto3
import json
import os
from datetime import datetime, timezone
from decimal import Decimal

ddb = boto3.resource("dynamodb")
sfn = boto3.client("stepfunctions")
table = ddb.Table(os.environ["REVIEWS_TABLE"])

def json_safe(value):
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, dict):
        return {k: json_safe(v) for k, v in value.items()}
    if isinstance(value, list):
        return [json_safe(v) for v in value]
    return value

def lambda_handler(event, context):
    review_id = (event.get("review_id") or event.get("pathParameters", {}).get("review_id"))
    decision = event["decision"]
    edited_response = event.get("edited_response")
    final_sentiment = event.get("final_sentiment")
    final_status = event.get("final_status", decision)

    item = table.get_item(Key={"review_id": review_id}).get("Item")
    if not item:
        raise ValueError("Review record not found")

    task_token = item["task_token"]
    now = datetime.now(timezone.utc).isoformat()

    table.update_item(
        Key={"review_id": review_id},
        UpdateExpression="SET #s = :s, reviewed_at = :r, decision = :d, edited_response = :e, final_sentiment = :f",
        ExpressionAttributeNames={"#s": "status"},
        ExpressionAttributeValues={
            ":s": "COMPLETED",
            ":r": now,
            ":d": decision,
            ":e": edited_response,
            ":f": final_sentiment
        }
    )

    output = {
        "feedback_id": item["feedback"]["feedback_id"],
        "sentiment": final_sentiment or item["feedback"]["sentiment"],
        "confidence": item["feedback"]["confidence"],
        "draft_response": edited_response or item["feedback"]["draft_response"],
        "final_status": final_status,
        "review_id": review_id
    }

    sfn.send_task_success(
        taskToken=task_token,
        output=json.dumps(json_safe(output))
    )

    return {
        "ok": True,
        "review_id": review_id
    }
