#!/usr/bin/env python3
"""
Cleanup SageMaker vLLM endpoint and associated resources.

Deletes in order: endpoint -> endpoint config -> model
to properly remove all resources and stop billing.

Usage:
    # Delete specific endpoint
    uv run cleanup <endpoint-name>

    # List all vLLM endpoints
    uv run cleanup --list

    # Delete all vLLM endpoints
    uv run cleanup --all
"""

import os
import sys
import time

import boto3
from botocore.exceptions import ClientError

REGION = os.environ.get("AWS_REGION", "eu-west-1")


def delete_endpoint(endpoint_name: str, sm_client) -> bool:
    """Delete SageMaker endpoint."""
    try:
        print(f"Deleting endpoint: {endpoint_name}")
        sm_client.delete_endpoint(EndpointName=endpoint_name)

        # Wait for deletion
        print("Waiting for endpoint deletion...")
        waiter = sm_client.get_waiter("endpoint_deleted")
        waiter.wait(
            EndpointName=endpoint_name,
            WaiterConfig={"Delay": 30, "MaxAttempts": 60},
        )
        print("Endpoint deleted.")
        return True
    except ClientError as e:
        if "Could not find endpoint" in str(e):
            print(f"Endpoint {endpoint_name} not found (already deleted).")
            return True
        raise


def delete_endpoint_config(config_name: str, sm_client) -> bool:
    """Delete SageMaker endpoint config."""
    try:
        print(f"Deleting endpoint config: {config_name}")
        sm_client.delete_endpoint_config(EndpointConfigName=config_name)
        print("Endpoint config deleted.")
        return True
    except ClientError as e:
        if "Could not find endpoint configuration" in str(e):
            print(f"Endpoint config {config_name} not found (already deleted).")
            return True
        raise


def delete_model(model_name: str, sm_client) -> bool:
    """Delete SageMaker model."""
    try:
        print(f"Deleting model: {model_name}")
        sm_client.delete_model(ModelName=model_name)
        print("Model deleted.")
        return True
    except ClientError as e:
        if "Could not find model" in str(e):
            print(f"Model {model_name} not found (already deleted).")
            return True
        raise


def cleanup_endpoint(endpoint_name: str) -> bool:
    """
    Delete endpoint and all associated resources.

    Args:
        endpoint_name: Name of the endpoint to delete

    Returns:
        True if cleanup was successful
    """
    sm = boto3.client("sagemaker", region_name=REGION)

    # Get endpoint details to find config and model names
    try:
        endpoint = sm.describe_endpoint(EndpointName=endpoint_name)
        config_name = endpoint["EndpointConfigName"]
    except ClientError as e:
        if "Could not find endpoint" in str(e):
            print(f"Endpoint {endpoint_name} not found.")
            return False
        raise

    # Get model name from config
    try:
        config = sm.describe_endpoint_config(EndpointConfigName=config_name)
        model_name = config["ProductionVariants"][0]["ModelName"]
    except ClientError:
        model_name = None

    print(f"\nResources to delete:")
    print(f"  Endpoint: {endpoint_name}")
    print(f"  Config: {config_name}")
    print(f"  Model: {model_name}")
    print()

    # Delete in order
    delete_endpoint(endpoint_name, sm)

    # Small delay to ensure endpoint is fully removed
    time.sleep(2)

    delete_endpoint_config(config_name, sm)

    if model_name:
        delete_model(model_name, sm)

    print("\nCleanup complete!")
    return True


def list_vllm_endpoints() -> list[dict]:
    """List all vLLM endpoints."""
    sm = boto3.client("sagemaker", region_name=REGION)

    response = sm.list_endpoints(
        SortBy="CreationTime",
        SortOrder="Descending",
        MaxResults=20,
    )

    vllm_endpoints = [
        ep for ep in response["Endpoints"] if "vllm" in ep["EndpointName"].lower()
    ]

    if not vllm_endpoints:
        print("No vLLM endpoints found.")
        return []

    print("vLLM Endpoints:")
    for ep in vllm_endpoints:
        print(f"  {ep['EndpointName']} ({ep['EndpointStatus']})")

    return vllm_endpoints


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: uv run cleanup <endpoint-name>")
        print("       uv run cleanup --list")
        print("       uv run cleanup --all")
        print()
        list_vllm_endpoints()
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--list":
        list_vllm_endpoints()
    elif arg == "--all":
        endpoints = list_vllm_endpoints()
        if endpoints:
            confirm = input("\nDelete ALL vLLM endpoints? [y/N]: ")
            if confirm.lower() == "y":
                for ep in endpoints:
                    cleanup_endpoint(ep["EndpointName"])
            else:
                print("Cancelled.")
    else:
        cleanup_endpoint(arg)


if __name__ == "__main__":
    main()
