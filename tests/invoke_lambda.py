#!/usr/bin/env python3
"""
Manual Lambda trigger script.

Usage:
    python tests/invoke_lambda.py --function-name <FUNCTION_NAME> [--region us-east-1]

The function name is printed as a CloudFormation output after `cdk deploy`.
"""
import argparse
import json
import sys

import boto3


def invoke_lambda(function_name: str, region: str, payload: dict) -> None:
    client = boto3.client("lambda", region_name=region)

    print(f"Invoking Lambda function: {function_name} (region: {region})")
    print(f"Payload: {json.dumps(payload, indent=2)}\n")

    response = client.invoke(
        FunctionName=function_name,
        InvocationType="RequestResponse",
        LogType="Tail",
        Payload=json.dumps(payload).encode(),
    )

    status_code = response["StatusCode"]
    payload_bytes = response["Payload"].read()
    result = json.loads(payload_bytes)

    print(f"HTTP Status Code : {status_code}")

    if "FunctionError" in response:
        print(f"Function Error   : {response['FunctionError']}")
        print(f"Error detail     : {json.dumps(result, indent=2)}")
        sys.exit(1)

    print(f"Response Body    :\n{json.dumps(result, indent=2)}")

    # Pretty-print the inner body if it exists
    if "body" in result:
        inner = json.loads(result["body"])
        print("\n── Execution summary ──────────────────────────────────────")
        print(f"  Bucket       : {inner.get('bucket')}")
        print(f"  Object count : {inner.get('object_count')}")
        print(f"  Objects      : {inner.get('objects')}")
        print(f"  SNS Msg ID   : {inner.get('sns_message_id')}")
        print(f"  Timestamp    : {inner.get('timestamp')}")


def main():
    parser = argparse.ArgumentParser(description="Manually invoke the serverless Lambda function")
    parser.add_argument(
        "--function-name",
        required=True,
        help="Lambda function name (from CDK output: LambdaFunctionName)",
    )
    parser.add_argument(
        "--region",
        default="us-east-1",
        help="AWS region (default: us-east-1)",
    )
    parser.add_argument(
        "--event-file",
        default=None,
        help="Path to a JSON file containing the test event (default: test_event.json)",
    )
    args = parser.parse_args()

    event_file = args.event_file or "test_event.json"
    try:
        with open(event_file) as f:
            payload = json.load(f)
    except FileNotFoundError:
        print(f"Event file '{event_file}' not found – using empty event {{}}")
        payload = {}

    invoke_lambda(args.function_name, args.region, payload)


if __name__ == "__main__":
    main()
