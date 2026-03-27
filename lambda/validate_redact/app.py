import json
import csv
import boto3
import os
import urllib.parse

s3 = boto3.client("s3")
comprehend = boto3.client("comprehend")

QUARANTINE_BUCKET = os.environ.get("QUARANTINE_BUCKET")

VALID_LANGS = {"en","es","fr","de","it","pt","ar","hi","ja","ko","zh","zh-TW"}


def normalize_language(lang):
    if not lang:
        return "en"

    lang = lang.lower()

    mapping = {
        "english": "en",
        "en-us": "en",
        "en-gb": "en",
        "spanish": "es",
        "french": "fr",
        "german": "de",
        "italian": "it",
        "portuguese": "pt",
        "japanese": "ja",
        "korean": "ko",
        "chinese": "zh",
        "zh-cn": "zh",
        "zh-tw": "zh-TW"
    }

    normalized = mapping.get(lang, lang)

    if normalized not in VALID_LANGS:
        return "en"

    return normalized


def redact_pii(text, language_code):
    if not text:
        return text

    try:
        response = comprehend.detect_pii_entities(
            Text=text,
            LanguageCode=language_code
        )

        entities = response.get("Entities", [])
        redacted_text = text

        # Replace from end to avoid index shifting
        for entity in sorted(entities, key=lambda x: x["BeginOffset"], reverse=True):
            start = entity["BeginOffset"]
            end = entity["EndOffset"]
            redacted_text = redacted_text[:start] + "[REDACTED]" + redacted_text[end:]

        return redacted_text

    except Exception as e:
        print(f"PII detection failed: {e}")
        return text  # fallback without breaking pipeline


def parse_csv(content):
    records = []
    reader = csv.DictReader(content.splitlines())
    for row in reader:
        records.append(dict(row))
    return records


def parse_json(content):
    data = json.loads(content)
    return data.get("records", [])


def load_file_from_s3(bucket, key):
    obj = s3.get_object(Bucket=bucket, Key=key)
    content = obj["Body"].read().decode("utf-8")

    if key.endswith(".csv"):
        return parse_csv(content)
    elif key.endswith(".json"):
        return parse_json(content)
    else:
        raise ValueError("Unsupported file format")


def quarantine_file(bucket, key, reason):
    if not QUARANTINE_BUCKET:
        return

    dest_key = f"quarantine/{key}"
    print(f"Quarantining file {key} due to: {reason}")

    s3.copy_object(
        Bucket=QUARANTINE_BUCKET,
        CopySource={"Bucket": bucket, "Key": key},
        Key=dest_key
    )


def lambda_handler(event, context):
    print("Received event:", json.dumps(event))

    try:
        bucket = event["detail"]["bucket"]["name"]
        key = urllib.parse.unquote_plus(event["detail"]["object"]["key"])

        records = load_file_from_s3(bucket, key)

    except Exception as e:
        print(f"Failed to load file: {e}")
        quarantine_file(bucket, key, str(e))
        raise

    cleaned_records = []

    for record in records:
        try:
            feedback_text = record.get("feedback_text")

            if not feedback_text:
                print("Skipping record with missing feedback_text")
                continue

            lang = normalize_language(record.get("language"))

            record["feedback_text"] = redact_pii(feedback_text, lang)

            # Ensure required fields exist
            record["feedback_id"] = record.get("feedback_id") or "unknown"
            record["language"] = lang

            cleaned_records.append(record)

        except Exception as e:
            print(f"Skipping bad record: {e}")
            continue

    if not cleaned_records:
        raise ValueError("No valid records found after processing")

    return {
        "records": cleaned_records
    }
