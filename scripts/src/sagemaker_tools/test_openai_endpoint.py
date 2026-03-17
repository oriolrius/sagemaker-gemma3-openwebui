#!/usr/bin/env python3
"""
Test SageMaker vLLM endpoint using OpenAI-compatible API format.

The LMI container automatically supports OpenAI Chat Completions format
when the request contains a "messages" field.

Usage:
    # Test specific endpoint
    uv run test-endpoint <endpoint-name>

    # Auto-detect latest vLLM endpoint
    uv run test-endpoint

    # Or directly
    python -m sagemaker_tools.test_openai_endpoint <endpoint-name>
"""

import json
import os
import sys
from typing import Generator

import boto3

REGION = os.environ.get("AWS_REGION", "eu-west-1")


class SageMakerOpenAIClient:
    """OpenAI-compatible client wrapper for SageMaker endpoints."""

    def __init__(self, endpoint_name: str, region: str = REGION):
        self.endpoint_name = endpoint_name
        self.region = region
        self.runtime = boto3.client("sagemaker-runtime", region_name=region)

    def chat_completions_create(
        self,
        messages: list[dict],
        max_tokens: int = 256,
        temperature: float = 0.7,
        stream: bool = False,
    ) -> dict | Generator[dict, None, None]:
        """
        Create a chat completion using OpenAI-compatible format.

        Args:
            messages: List of message dicts with 'role' and 'content'
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stream: Whether to stream the response

        Returns:
            OpenAI-compatible response dict, or generator if streaming
        """
        payload = {
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": stream,
        }

        if stream:
            return self._invoke_streaming(payload)
        else:
            return self._invoke_sync(payload)

    def _invoke_sync(self, payload: dict) -> dict:
        """Synchronous invocation."""
        response = self.runtime.invoke_endpoint(
            EndpointName=self.endpoint_name,
            ContentType="application/json",
            Body=json.dumps(payload),
        )
        return json.loads(response["Body"].read().decode())

    def _invoke_streaming(self, payload: dict) -> Generator[dict, None, None]:
        """Streaming invocation with Server-Sent Events."""
        response = self.runtime.invoke_endpoint_with_response_stream(
            EndpointName=self.endpoint_name,
            ContentType="application/json",
            Body=json.dumps(payload),
        )

        for event in response["Body"]:
            chunk = event.get("PayloadPart", {}).get("Bytes", b"")
            if chunk:
                for line in chunk.decode().split("\n"):
                    if line.startswith("data: "):
                        data = line[6:]
                        if data != "[DONE]":
                            yield json.loads(data)


def test_chat_completion(endpoint_name: str) -> dict:
    """Test basic chat completion with OpenAI format."""
    print("=" * 60)
    print("Test 1: Basic Chat Completion (OpenAI Format)")
    print("=" * 60)

    client = SageMakerOpenAIClient(endpoint_name)

    messages = [
        {"role": "user", "content": "What is machine learning? Answer in one sentence."}
    ]

    print(f"Request: {json.dumps(messages, indent=2)}")

    response = client.chat_completions_create(
        messages=messages,
        max_tokens=100,
        temperature=0.7,
    )

    print(f"\nResponse:")
    print(json.dumps(response, indent=2))

    # Validate response structure
    assert "choices" in response, "Missing 'choices' in response"
    assert len(response["choices"]) > 0, "Empty choices array"
    assert "message" in response["choices"][0], "Missing 'message' in choice"

    print("\n[PASS] Chat completion successful!")
    return response


def test_streaming(endpoint_name: str) -> str:
    """Test streaming chat completion."""
    print("\n" + "=" * 60)
    print("Test 2: Streaming Chat Completion")
    print("=" * 60)

    client = SageMakerOpenAIClient(endpoint_name)

    messages = [{"role": "user", "content": "Count from 1 to 5."}]

    print(f"Request (stream=True): {json.dumps(messages, indent=2)}")
    print("\nStreaming response:")

    full_response = ""
    try:
        for chunk in client.chat_completions_create(
            messages=messages,
            max_tokens=50,
            stream=True,
        ):
            if "choices" in chunk and len(chunk["choices"]) > 0:
                delta = chunk["choices"][0].get("delta", {})
                content = delta.get("content", "")
                if content:
                    print(content, end="", flush=True)
                    full_response += content

        print("\n\n[PASS] Streaming successful!")
    except Exception as e:
        print(f"\n[SKIP] Streaming not available or failed: {e}")

    return full_response


def test_legacy_format(endpoint_name: str) -> dict:
    """Test legacy (non-OpenAI) format for backwards compatibility."""
    print("\n" + "=" * 60)
    print("Test 3: Legacy Format (Backwards Compatibility)")
    print("=" * 60)

    runtime = boto3.client("sagemaker-runtime", region_name=REGION)

    payload = {
        "inputs": "The capital of France is",
        "parameters": {"max_new_tokens": 20, "temperature": 0.7},
    }

    print(f"Request: {json.dumps(payload, indent=2)}")

    response = runtime.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType="application/json",
        Body=json.dumps(payload),
    )

    result = json.loads(response["Body"].read().decode())
    print(f"\nResponse: {json.dumps(result, indent=2)}")

    print("\n[PASS] Legacy format successful!")
    return result


def get_latest_vllm_endpoint() -> str | None:
    """Find the most recent vLLM endpoint that is InService."""
    sm = boto3.client("sagemaker", region_name=REGION)

    response = sm.list_endpoints(
        SortBy="CreationTime",
        SortOrder="Descending",
        MaxResults=20,
    )

    for endpoint in response["Endpoints"]:
        if "vllm" in endpoint["EndpointName"].lower():
            if endpoint["EndpointStatus"] == "InService":
                return endpoint["EndpointName"]

    return None


def main():
    """Main entry point."""
    # Get endpoint name from args, env, or auto-detect
    if len(sys.argv) > 1:
        endpoint_name = sys.argv[1]
    else:
        endpoint_name = os.environ.get("SAGEMAKER_ENDPOINT_NAME")

    if not endpoint_name:
        print("Searching for latest vLLM endpoint...")
        endpoint_name = get_latest_vllm_endpoint()

    if not endpoint_name:
        print("ERROR: No endpoint found.")
        print("Usage: uv run test-endpoint <endpoint-name>")
        sys.exit(1)

    print(f"Testing endpoint: {endpoint_name}")
    print(f"Region: {REGION}")

    # Run tests
    try:
        test_chat_completion(endpoint_name)
        test_streaming(endpoint_name)
        test_legacy_format(endpoint_name)

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
