"""
Unit tests for the Lambda handler function.

These tests mock both boto3 clients so no AWS credentials are required.
Run with:  pytest tests/test_handler.py -v
"""
import importlib
import json
import sys
import types
from unittest.mock import MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers: build a minimal boto3 stub so we can import the handler without
# real AWS credentials.
# ---------------------------------------------------------------------------

def _make_paginator(pages):
    """Return a mock paginator whose .paginate() yields the given pages."""
    paginator = MagicMock()
    paginator.paginate.return_value = iter(pages)
    return paginator


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def lambda_env(monkeypatch):
    """Set required environment variables before importing the handler."""
    monkeypatch.setenv("BUCKET_NAME", "test-bucket")
    monkeypatch.setenv("SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:123456789012:test-topic")


@pytest.fixture()
def handler_module(lambda_env):
    """
    Import (or reimport) the handler module with mocked boto3 clients.
    Uses importlib so env vars set by lambda_env are already in place.
    """
    s3_mock = MagicMock()
    sns_mock = MagicMock()

    # Default: bucket with two objects
    s3_mock.get_paginator.return_value = _make_paginator(
        [{"Contents": [{"Key": "sample_files/sample1.txt", "Size": 255},
                        {"Key": "sample_files/sample2.txt", "Size": 248}]}]
    )
    sns_mock.publish.return_value = {"MessageId": "mock-message-id-1234"}

    with patch("boto3.client") as boto3_client:
        def _client_factory(service, **_kwargs):
            if service == "s3":
                return s3_mock
            if service == "sns":
                return sns_mock
            raise ValueError(f"Unexpected service: {service}")

        boto3_client.side_effect = _client_factory

        # Force reimport so module-level boto3.client() calls pick up mocks
        if "lambda.handler" in sys.modules:
            del sys.modules["lambda.handler"]
        if "handler" in sys.modules:
            del sys.modules["handler"]

        sys.path.insert(0, "lambda")
        import handler as h
        yield h, s3_mock, sns_mock
        sys.path.pop(0)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestLambdaHandler:

    def test_returns_200_on_success(self, handler_module):
        h, s3_mock, sns_mock = handler_module
        result = h.lambda_handler({}, MagicMock())
        assert result["statusCode"] == 200

    def test_response_body_contains_object_count(self, handler_module):
        h, s3_mock, sns_mock = handler_module
        result = h.lambda_handler({}, MagicMock())
        body = json.loads(result["body"])
        assert body["object_count"] == 2

    def test_response_body_lists_object_keys(self, handler_module):
        h, s3_mock, sns_mock = handler_module
        result = h.lambda_handler({}, MagicMock())
        body = json.loads(result["body"])
        assert "sample_files/sample1.txt" in body["objects"]
        assert "sample_files/sample2.txt" in body["objects"]

    def test_response_body_contains_bucket_name(self, handler_module):
        h, s3_mock, sns_mock = handler_module
        result = h.lambda_handler({}, MagicMock())
        body = json.loads(result["body"])
        assert body["bucket"] == "test-bucket"

    def test_sns_publish_called_once(self, handler_module):
        h, s3_mock, sns_mock = handler_module
        h.lambda_handler({}, MagicMock())
        sns_mock.publish.assert_called_once()

    def test_sns_message_id_in_response(self, handler_module):
        h, s3_mock, sns_mock = handler_module
        result = h.lambda_handler({}, MagicMock())
        body = json.loads(result["body"])
        assert body["sns_message_id"] == "mock-message-id-1234"

    def test_empty_bucket(self, lambda_env):
        """Lambda should handle an empty bucket gracefully."""
        s3_mock = MagicMock()
        sns_mock = MagicMock()
        s3_mock.get_paginator.return_value = _make_paginator([{"Contents": []}])
        sns_mock.publish.return_value = {"MessageId": "empty-bucket-msg-id"}

        with patch("boto3.client") as boto3_client:
            def _client_factory(service, **_kwargs):
                return s3_mock if service == "s3" else sns_mock
            boto3_client.side_effect = _client_factory

            if "handler" in sys.modules:
                del sys.modules["handler"]
            sys.path.insert(0, "lambda")
            import handler as h
            sys.path.pop(0)

            result = h.lambda_handler({}, MagicMock())
            body = json.loads(result["body"])
            assert result["statusCode"] == 200
            assert body["object_count"] == 0
            assert body["objects"] == []
