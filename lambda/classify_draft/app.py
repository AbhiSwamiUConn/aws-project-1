import boto3
import json
import os
import re

bedrock = boto3.client("bedrock-runtime")
MODEL_ID = os.environ["BEDROCK_MODEL_ID"]

def extract_json(text):
    text = text.strip()
    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"```$", "", text)
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("Model did not return JSON")
    return json.loads(text[start:end + 1])

def build_prompt(record):
    return f"""
You are a customer support triage assistant.

Return ONLY valid JSON with this schema:
{{
  "feedback_id": string,
  "sentiment": "Positive" | "Negative" | "Urgent",
  "confidence": number,
  "summary": string,
  "draft_response": string,
  "reason": string
}}

Rules:
- Use "Urgent" for outages, safety-critical issues, account compromise, or severe escalation.
- Confidence must be between 0 and 1.
- Draft response must be concise, empathetic, and useful.
- Do not use markdown fences.

Feedback record:
{json.dumps(record, ensure_ascii=False)}
""".strip()

def lambda_handler(event, context):
    prompt = build_prompt(event)

    response = bedrock.converse(
        modelId=MODEL_ID,
        messages=[
            {
                "role": "user",
                "content": [{"text": prompt}]
            }
        ],
        inferenceConfig={
            "temperature": 0,
            "maxTokens": 500
        }
    )

    text = "".join(
        part.get("text", "")
        for part in response["output"]["message"]["content"]
    )

    parsed = extract_json(text)

    return {
        "feedback_id": parsed["feedback_id"],
        "sentiment": parsed["sentiment"],
        "confidence": parsed["confidence"],
        "summary": parsed["summary"],
        "draft_response": parsed["draft_response"],
        "reason": parsed["reason"]
    }
