#!/usr/bin/env python3
"""
Deploy LLM to SageMaker with vLLM backend and OpenAI-compatible API.

Uses AWS DJL-LMI container with vLLM rolling batch inference.
The endpoint automatically supports OpenAI Chat Completions API format
when requests include a "messages" field.

Usage:
    # Using uv
    uv run deploy-vllm

    # Or directly
    python -m sagemaker_tools.deploy_vllm

Environment variables:
    AWS_REGION: AWS region (default: eu-west-1)
    HF_MODEL_ID: HuggingFace model ID (default: distilgpt2)
    INSTANCE_TYPE: SageMaker instance type (default: ml.g4dn.xlarge)
    SAGEMAKER_ROLE_ARN: IAM role ARN for SageMaker (auto-detected if not set)
"""

import os
from datetime import datetime

import boto3

# Configuration
REGION = os.environ.get("AWS_REGION", "eu-west-1")
MODEL_ID = os.environ.get("HF_MODEL_ID", "distilgpt2")
INSTANCE_TYPE = os.environ.get("INSTANCE_TYPE", "ml.g4dn.xlarge")

# LMI Container image (0.28.0-lmi10.0.0 = vLLM backend)
LMI_IMAGE_TAG = "0.28.0-lmi10.0.0-cu124"
ECR_REGISTRY = "763104351884"  # AWS Deep Learning Containers registry


def get_account_id() -> str:
    """Get AWS account ID."""
    sts = boto3.client("sts", region_name=REGION)
    return sts.get_caller_identity()["Account"]


def get_default_bucket() -> str:
    """Get or create the default SageMaker bucket."""
    account_id = get_account_id()
    bucket_name = f"sagemaker-{REGION}-{account_id}"

    s3 = boto3.client("s3", region_name=REGION)
    try:
        s3.head_bucket(Bucket=bucket_name)
    except s3.exceptions.ClientError:
        print(f"Creating bucket: {bucket_name}")
        if REGION == "us-east-1":
            s3.create_bucket(Bucket=bucket_name)
        else:
            s3.create_bucket(
                Bucket=bucket_name,
                CreateBucketConfiguration={"LocationConstraint": REGION},
            )

    return bucket_name


def get_role_arn() -> str:
    """Get SageMaker execution role ARN."""
    # Check environment variable first
    if role_arn := os.environ.get("SAGEMAKER_ROLE_ARN"):
        return role_arn

    iam = boto3.client("iam", region_name=REGION)

    # Try common SageMaker role names
    role_patterns = [
        "AmazonSageMakerAdminIAMExecutionRole",
        "AmazonSageMaker-ExecutionRole",
        "SageMakerExecutionRole",
    ]

    for role_name in role_patterns:
        try:
            response = iam.get_role(RoleName=role_name)
            return response["Role"]["Arn"]
        except iam.exceptions.NoSuchEntityException:
            continue

    raise RuntimeError(
        "Could not find SageMaker execution role. "
        "Set SAGEMAKER_ROLE_ARN environment variable."
    )


def get_lmi_image_uri() -> str:
    """Get LMI container image URI for the region."""
    return f"{ECR_REGISTRY}.dkr.ecr.{REGION}.amazonaws.com/djl-inference:{LMI_IMAGE_TAG}"


def deploy_vllm_endpoint() -> tuple[str, str, str]:
    """Deploy SageMaker endpoint with vLLM backend.

    Returns:
        Tuple of (endpoint_name, model_name, endpoint_config_name)
    """
    sm = boto3.client("sagemaker", region_name=REGION)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")

    # Create resource names
    safe_model_name = MODEL_ID.replace("/", "-").replace(".", "-")
    model_name = f"vllm-{safe_model_name}-{timestamp}"
    endpoint_config_name = f"vllm-config-{timestamp}"
    endpoint_name = f"vllm-endpoint-{timestamp}"

    role_arn = get_role_arn()
    image_uri = get_lmi_image_uri()

    print(f"Region: {REGION}")
    print(f"Role: {role_arn}")
    print(f"Container: {image_uri}")
    print(f"Model: {MODEL_ID}")
    print(f"Instance: {INSTANCE_TYPE}")

    # Environment variables for vLLM with LMI
    # OpenAI API compatibility is automatic when request has "messages" field
    environment = {
        # Model configuration
        "HF_MODEL_ID": MODEL_ID,
        # vLLM backend configuration
        "OPTION_ROLLING_BATCH": "vllm",
        "OPTION_DTYPE": "fp16",
        "OPTION_MAX_MODEL_LEN": "1024",  # distilgpt2 max context
        "OPTION_TENSOR_PARALLEL_DEGREE": "1",
        # Memory management
        "OPTION_GPU_MEMORY_UTILIZATION": "0.9",
        # Timeout settings
        "OPTION_MODEL_LOADING_TIMEOUT": "1800",
    }

    # Create model
    print(f"\nCreating model: {model_name}")
    sm.create_model(
        ModelName=model_name,
        PrimaryContainer={
            "Image": image_uri,
            "Environment": environment,
        },
        ExecutionRoleArn=role_arn,
    )

    # Create endpoint config
    print(f"Creating endpoint config: {endpoint_config_name}")
    sm.create_endpoint_config(
        EndpointConfigName=endpoint_config_name,
        ProductionVariants=[
            {
                "VariantName": "AllTraffic",
                "ModelName": model_name,
                "InitialInstanceCount": 1,
                "InstanceType": INSTANCE_TYPE,
                "InitialVariantWeight": 1.0,
                "ContainerStartupHealthCheckTimeoutInSeconds": 900,
                "ModelDataDownloadTimeoutInSeconds": 1200,
            }
        ],
    )

    # Create endpoint
    print(f"Creating endpoint: {endpoint_name}")
    sm.create_endpoint(
        EndpointName=endpoint_name,
        EndpointConfigName=endpoint_config_name,
    )

    return endpoint_name, model_name, endpoint_config_name


def main():
    """Main entry point."""
    endpoint_name, model_name, config_name = deploy_vllm_endpoint()

    print(f"\n{'=' * 60}")
    print("Deployment initiated!")
    print(f"{'=' * 60}")
    print(f"Endpoint Name: {endpoint_name}")
    print(f"Model Name: {model_name}")
    print(f"Config Name: {config_name}")
    print(f"\nWait for endpoint to be ready:")
    print(f"  aws sagemaker wait endpoint-in-service --endpoint-name {endpoint_name}")
    print(f"\nTest with OpenAI-compatible API:")
    print(f"  uv run test-endpoint {endpoint_name}")
    print(f"\nCleanup when done:")
    print(f"  uv run cleanup {endpoint_name}")


if __name__ == "__main__":
    main()
