"""Lambda handler for OpenAI-compatible API proxy to SageMaker."""

import base64
import json
import os
from typing import Any

import boto3

# Environment configuration
SAGEMAKER_ENDPOINT_NAME = os.environ.get("SAGEMAKER_ENDPOINT_NAME", "")
AWS_REGION = os.environ.get("AWS_REGION", "eu-west-1")

# Lazy-initialized SageMaker client
_sagemaker_runtime = None


def get_sagemaker_client():
    """Get or create SageMaker runtime client."""
    global _sagemaker_runtime
    if _sagemaker_runtime is None:
        _sagemaker_runtime = boto3.client("sagemaker-runtime", region_name=AWS_REGION)
    return _sagemaker_runtime


def create_response(status_code: int, body: dict, headers: dict | None = None) -> dict:
    """Create a Lambda proxy response."""
    default_headers = {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
    }
    if headers:
        default_headers.update(headers)

    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(body) if isinstance(body, dict) else body,
    }


def create_error_response(status_code: int, message: str, error_type: str = "server_error") -> dict:
    """Create an error response in OpenAI format."""
    return create_response(status_code, {"error": {"message": message, "type": error_type}})


def handle_models_request() -> dict:
    """Handle GET /v1/models request."""
    return create_response(
        200,
        {
            "object": "list",
            "data": [
                {
                    "id": SAGEMAKER_ENDPOINT_NAME,
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": "sagemaker",
                }
            ],
        },
    )


def handle_cors_request() -> dict:
    """Handle OPTIONS request for CORS preflight."""
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
        },
        "body": "",
    }


def parse_request_body(event: dict) -> dict:
    """Parse request body from Lambda event."""
    body = event.get("body", "{}")

    if event.get("isBase64Encoded"):
        body = base64.b64decode(body).decode("utf-8")

    return json.loads(body)


def messages_to_prompt(messages: list[dict]) -> str:
    """Convert OpenAI messages format to a simple prompt string."""
    return "\n".join([m.get("content", "") for m in messages])


def invoke_sagemaker(messages: list[dict], max_tokens: int = 100, temperature: float = 0.7) -> dict:
    """Invoke SageMaker TGI endpoint."""
    client = get_sagemaker_client()

    prompt = messages_to_prompt(messages)

    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": max_tokens,
            "temperature": temperature,
            "do_sample": True,
        },
    }

    response = client.invoke_endpoint(
        EndpointName=SAGEMAKER_ENDPOINT_NAME,
        ContentType="application/json",
        Body=json.dumps(payload),
    )

    result = json.loads(response["Body"].read().decode("utf-8"))

    # TGI returns a list of generated texts
    if isinstance(result, list) and result:
        text = result[0].get("generated_text", "")
        # TGI includes the input prompt in the output — strip it
        if text.startswith(prompt):
            text = text[len(prompt):].strip()
        return {"generated_text": text}

    return {"generated_text": result.get("generated_text", "")}


def create_chat_completion_response(
    request_id: str,
    generated_text: str,
    prompt: str,
) -> dict:
    """Create OpenAI-compatible chat completion response."""
    prompt_tokens = len(prompt.split())
    completion_tokens = len(generated_text.split())

    return {
        "id": f"chatcmpl-{request_id}",
        "object": "chat.completion",
        "model": SAGEMAKER_ENDPOINT_NAME,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": generated_text,
                },
                "finish_reason": "stop",
            }
        ],
        "usage": {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total_tokens": prompt_tokens + completion_tokens,
        },
    }


def handle_chat_completion(event: dict, context: Any) -> dict:
    """Handle POST /v1/chat/completions request."""
    try:
        request_body = parse_request_body(event)
    except (json.JSONDecodeError, ValueError) as e:
        return create_error_response(400, f"Invalid JSON: {e}", "invalid_request_error")

    messages = request_body.get("messages", [])
    max_tokens = request_body.get("max_tokens", 100)
    temperature = request_body.get("temperature", 0.7)

    try:
        result = invoke_sagemaker(messages, max_tokens, temperature)
    except Exception as e:
        return create_error_response(500, str(e), "server_error")

    generated_text = result.get("generated_text", "")
    prompt = messages_to_prompt(messages)
    request_id = getattr(context, "aws_request_id", "local-test")
    response_body = create_chat_completion_response(request_id, generated_text, prompt)
    return create_response(200, response_body)


def lambda_handler(event: dict, context: Any) -> dict:
    """Main Lambda handler - routes requests to appropriate handlers."""
    http_method = event.get("requestContext", {}).get("http", {}).get("method", "POST")
    path = event.get("rawPath", "/")

    # GET /v1/models
    if http_method == "GET" and "/models" in path:
        return handle_models_request()

    # OPTIONS (CORS preflight)
    if http_method == "OPTIONS":
        return handle_cors_request()

    # POST /v1/chat/completions or /v1/completions
    if http_method == "POST":
        return handle_chat_completion(event, context)

    return create_error_response(404, "Not found", "not_found")
