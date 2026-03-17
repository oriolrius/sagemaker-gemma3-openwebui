#!/usr/bin/env python3
"""
Test API Gateway endpoint with OpenAI-compatible API format.

Tests the Lambda proxy in front of SageMaker, which handles
SigV4 signing and request transformation.

Usage:
    uv run python -m sagemaker_tools.test_api_gateway <api-gateway-url>

    # Example:
    uv run python -m sagemaker_tools.test_api_gateway https://abc123.execute-api.eu-west-1.amazonaws.com
"""

import json
import sys
from urllib.parse import urljoin

import urllib.request
import urllib.error


def test_models_endpoint(base_url: str) -> dict:
    """Test GET /v1/models endpoint."""
    print("=" * 60)
    print("Test 1: List Models (GET /v1/models)")
    print("=" * 60)

    url = urljoin(base_url.rstrip("/") + "/", "v1/models")
    print(f"URL: {url}")

    req = urllib.request.Request(url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read().decode())
            print(f"\nResponse ({response.status}):")
            print(json.dumps(result, indent=2))

            assert "data" in result, "Missing 'data' in response"
            assert len(result["data"]) > 0, "Empty models list"

            print("\n[PASS] Models endpoint successful!")
            return result
    except urllib.error.HTTPError as e:
        print(f"\n[FAIL] HTTP Error {e.code}: {e.read().decode()}")
        raise


def test_chat_completions(base_url: str) -> dict:
    """Test POST /v1/chat/completions endpoint."""
    print("\n" + "=" * 60)
    print("Test 2: Chat Completion (POST /v1/chat/completions)")
    print("=" * 60)

    url = urljoin(base_url.rstrip("/") + "/", "v1/chat/completions")
    print(f"URL: {url}")

    payload = {
        "messages": [
            {"role": "user", "content": "The future of artificial intelligence is"}
        ],
        "max_tokens": 50,
        "temperature": 0.7,
    }

    print(f"\nRequest:")
    print(json.dumps(payload, indent=2))

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode())
            print(f"\nResponse ({response.status}):")
            print(json.dumps(result, indent=2))

            assert "choices" in result, "Missing 'choices' in response"
            assert len(result["choices"]) > 0, "Empty choices array"
            assert "message" in result["choices"][0], "Missing 'message' in choice"

            print("\n[PASS] Chat completion successful!")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"\n[FAIL] HTTP Error {e.code}: {error_body}")
        raise


def test_completions_legacy(base_url: str) -> dict:
    """Test POST /v1/completions endpoint (text completion format)."""
    print("\n" + "=" * 60)
    print("Test 3: Text Completion (POST /v1/completions)")
    print("=" * 60)

    url = urljoin(base_url.rstrip("/") + "/", "v1/completions")
    print(f"URL: {url}")

    payload = {
        "messages": [
            {"role": "user", "content": "Q: What is the capital of France?\nA:"}
        ],
        "max_tokens": 30,
        "temperature": 0.5,
    }

    print(f"\nRequest:")
    print(json.dumps(payload, indent=2))

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={"Content-Type": "application/json"},
    )

    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            result = json.loads(response.read().decode())
            print(f"\nResponse ({response.status}):")
            print(json.dumps(result, indent=2))

            print("\n[PASS] Completions endpoint successful!")
            return result
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"\n[FAIL] HTTP Error {e.code}: {error_body}")
        raise


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python -m sagemaker_tools.test_api_gateway <api-gateway-url>")
        print()
        print("Example:")
        print("  python -m sagemaker_tools.test_api_gateway https://abc123.execute-api.eu-west-1.amazonaws.com")
        sys.exit(1)

    base_url = sys.argv[1]
    print(f"Testing API Gateway: {base_url}")
    print()

    try:
        test_models_endpoint(base_url)
        test_chat_completions(base_url)
        test_completions_legacy(base_url)

        print("\n" + "=" * 60)
        print("ALL TESTS PASSED!")
        print("=" * 60)
    except Exception as e:
        print(f"\n[FAIL] Test failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
