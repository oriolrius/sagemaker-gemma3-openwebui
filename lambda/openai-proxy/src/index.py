"""Lambda entry point - AWS Lambda calls index.lambda_handler."""

from openai_proxy.handler import lambda_handler

# Re-export for Lambda runtime
__all__ = ["lambda_handler"]
