"""Unit tests for Lambda handler functions."""

import base64
import json
import os
from unittest.mock import MagicMock, patch

import pytest


# Set environment variables before importing handler
os.environ["SAGEMAKER_ENDPOINT_NAME"] = "test-endpoint"
os.environ["AWS_REGION"] = "us-east-1"

from openai_proxy.handler import (
    create_chat_completion_response,
    create_error_response,
    create_response,
    handle_chat_completion,
    handle_cors_request,
    handle_models_request,
    lambda_handler,
    messages_to_prompt,
    parse_request_body,
)


class TestCreateResponse:
    """Tests for create_response function."""

    def test_basic_response(self):
        response = create_response(200, {"message": "ok"})

        assert response["statusCode"] == 200
        assert response["headers"]["Content-Type"] == "application/json"
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert json.loads(response["body"]) == {"message": "ok"}

    def test_custom_headers(self):
        response = create_response(201, {"id": "123"}, {"X-Custom": "value"})

        assert response["headers"]["X-Custom"] == "value"
        assert response["headers"]["Content-Type"] == "application/json"


class TestCreateErrorResponse:
    """Tests for create_error_response function."""

    def test_error_response_format(self):
        response = create_error_response(400, "Bad request", "invalid_request_error")

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["message"] == "Bad request"
        assert body["error"]["type"] == "invalid_request_error"

    def test_default_error_type(self):
        response = create_error_response(500, "Internal error")

        body = json.loads(response["body"])
        assert body["error"]["type"] == "server_error"


class TestHandleModelsRequest:
    """Tests for handle_models_request function."""

    def test_returns_model_list(self):
        response = handle_models_request()

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["object"] == "list"
        assert len(body["data"]) == 1
        assert body["data"][0]["id"] == "test-endpoint"
        assert body["data"][0]["object"] == "model"


class TestHandleCorsRequest:
    """Tests for handle_cors_request function."""

    def test_cors_headers(self):
        response = handle_cors_request()

        assert response["statusCode"] == 200
        assert response["headers"]["Access-Control-Allow-Origin"] == "*"
        assert "GET" in response["headers"]["Access-Control-Allow-Methods"]
        assert "POST" in response["headers"]["Access-Control-Allow-Methods"]
        assert response["body"] == ""


class TestParseRequestBody:
    """Tests for parse_request_body function."""

    def test_parse_json_body(self):
        event = {"body": '{"messages": [{"role": "user", "content": "hello"}]}'}

        result = parse_request_body(event)

        assert result["messages"][0]["content"] == "hello"

    def test_parse_base64_body(self):
        original = '{"test": "value"}'
        encoded = base64.b64encode(original.encode()).decode()
        event = {"body": encoded, "isBase64Encoded": True}

        result = parse_request_body(event)

        assert result["test"] == "value"

    def test_empty_body(self):
        event = {}

        result = parse_request_body(event)

        assert result == {}


class TestMessagesToPrompt:
    """Tests for messages_to_prompt function."""

    def test_single_message(self):
        messages = [{"role": "user", "content": "Hello world"}]

        result = messages_to_prompt(messages)

        assert result == "Hello world"

    def test_multiple_messages(self):
        messages = [
            {"role": "system", "content": "You are helpful"},
            {"role": "user", "content": "Hi"},
        ]

        result = messages_to_prompt(messages)

        assert result == "You are helpful\nHi"

    def test_empty_messages(self):
        result = messages_to_prompt([])
        assert result == ""


class TestCreateChatCompletionResponse:
    """Tests for create_chat_completion_response function."""

    def test_response_format(self):
        response = create_chat_completion_response(
            request_id="abc123",
            generated_text="This is the response",
            prompt="Hello",
        )

        assert response["id"] == "chatcmpl-abc123"
        assert response["object"] == "chat.completion"
        assert response["choices"][0]["message"]["role"] == "assistant"
        assert response["choices"][0]["message"]["content"] == "This is the response"
        assert response["choices"][0]["finish_reason"] == "stop"
        assert "usage" in response
        assert response["usage"]["total_tokens"] == response["usage"]["prompt_tokens"] + response["usage"]["completion_tokens"]


class TestLambdaHandler:
    """Tests for main lambda_handler function."""

    def test_get_models(self):
        event = {
            "requestContext": {"http": {"method": "GET"}},
            "rawPath": "/v1/models",
        }

        response = lambda_handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["object"] == "list"

    def test_options_cors(self):
        event = {
            "requestContext": {"http": {"method": "OPTIONS"}},
            "rawPath": "/v1/chat/completions",
        }

        response = lambda_handler(event, None)

        assert response["statusCode"] == 200
        assert "Access-Control-Allow-Methods" in response["headers"]

    @patch("openai_proxy.handler.invoke_sagemaker")
    def test_post_chat_completions(self, mock_invoke):
        mock_invoke.return_value = {"generated_text": "Generated response"}

        mock_context = MagicMock()
        mock_context.aws_request_id = "test-123"

        event = {
            "requestContext": {"http": {"method": "POST"}},
            "rawPath": "/v1/chat/completions",
            "body": json.dumps({
                "messages": [{"role": "user", "content": "Hello"}],
                "max_tokens": 50,
            }),
        }

        response = lambda_handler(event, mock_context)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        assert body["choices"][0]["message"]["content"] == "Generated response"
        mock_invoke.assert_called_once_with([{"role": "user", "content": "Hello"}], 50, 0.7)

    def test_invalid_json_body(self):
        event = {
            "requestContext": {"http": {"method": "POST"}},
            "rawPath": "/v1/chat/completions",
            "body": "not valid json",
        }

        response = lambda_handler(event, None)

        assert response["statusCode"] == 400
        body = json.loads(response["body"])
        assert body["error"]["type"] == "invalid_request_error"

    def test_unknown_route(self):
        event = {
            "requestContext": {"http": {"method": "DELETE"}},
            "rawPath": "/v1/unknown",
        }

        response = lambda_handler(event, None)

        assert response["statusCode"] == 404


class TestHandleChatCompletion:
    """Tests for handle_chat_completion function."""

    @patch("openai_proxy.handler.invoke_sagemaker")
    def test_sagemaker_error(self, mock_invoke):
        mock_invoke.side_effect = Exception("SageMaker error")

        mock_context = MagicMock()
        mock_context.aws_request_id = "test-123"

        event = {
            "body": json.dumps({"messages": [{"role": "user", "content": "Hi"}]}),
        }

        response = handle_chat_completion(event, mock_context)

        assert response["statusCode"] == 500
        body = json.loads(response["body"])
        assert "SageMaker error" in body["error"]["message"]
