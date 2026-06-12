"""
Lambda handler: lists all objects in the configured S3 bucket and publishes
a summary message to an SNS topic.
"""
import json
import logging
import os
from datetime import datetime, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

BUCKET_NAME = os.environ["BUCKET_NAME"]
SNS_TOPIC_ARN = os.environ["SNS_TOPIC_ARN"]

s3_client = boto3.client("s3")
sns_client = boto3.client("sns")


def lambda_handler(event, context):
    """Entry point for the Lambda function."""
    logger.info("Lambda invoked. Event: %s", json.dumps(event))

    # 1. List all objects in the S3 bucket
    objects = _list_all_objects(BUCKET_NAME)
    object_count = len(objects)
    logger.info("Found %d object(s) in bucket '%s'", object_count, BUCKET_NAME)

    # 2. Build a human-readable summary
    timestamp = datetime.now(tz=timezone.utc).isoformat()
    object_list_text = "\n".join(
        f"  - {obj['Key']} ({obj['Size']} bytes)" for obj in objects
    ) or "  (bucket is empty)"

    message = (
        f"Serverless App – Execution Report\n"
        f"Timestamp : {timestamp}\n"
        f"Bucket    : {BUCKET_NAME}\n"
        f"Objects   : {object_count}\n"
        f"\nObject listing:\n{object_list_text}"
    )

    # 3. Publish to SNS
    response = sns_client.publish(
        TopicArn=SNS_TOPIC_ARN,
        Subject=f"S3 Bucket Report – {object_count} object(s) found",
        Message=message,
    )
    logger.info("SNS publish response: %s", response)

    return {
        "statusCode": 200,
        "body": json.dumps(
            {
                "bucket": BUCKET_NAME,
                "object_count": object_count,
                "objects": [obj["Key"] for obj in objects],
                "sns_message_id": response["MessageId"],
                "timestamp": timestamp,
            }
        ),
    }


def _list_all_objects(bucket_name: str) -> list:
    """Return a flat list of all objects (handles pagination automatically)."""
    paginator = s3_client.get_paginator("list_objects_v2")
    objects = []
    for page in paginator.paginate(Bucket=bucket_name):
        objects.extend(page.get("Contents", []))
    return objects
