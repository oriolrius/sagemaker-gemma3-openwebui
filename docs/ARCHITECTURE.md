# Architecture (v2.x — Fargate)

![Architecture Diagram](architecture.png)

## Overview

```
Browser -> OpenWebUI (Fargate/ALB) -> API Gateway -> Lambda -> SageMaker TGI (ml.g5.xlarge)
```

Single CloudFormation stack deploys up to 23 resources in `eu-west-1` (22 when `ExternalSageMakerRoleArn` is provided). All resources are standalone — no external dependencies.

## Components

### SageMaker TGI Endpoint
- **Instance**: ml.g5.xlarge (NVIDIA A10G, 24 GB GDDR6, Ampere)
- **Container**: `huggingface-pytorch-tgi-inference:2.7.0-tgi3.3.6-gpu-py311-cu124-ubuntu22.04-v1.0`
- **Precision**: bfloat16 (required for Gemma 3)
- **Model**: `oriolrius/myemoji-gemma-3-270m-it` (configurable)
- **Config**: 1 GPU, 1024 max input tokens, 2048 max total tokens, 4 max concurrent requests

### Lambda (OpenAI Proxy)
- **Runtime**: Python 3.11, 256 MB, 60s timeout
- **Purpose**: Translates OpenAI API format (`/v1/chat/completions`, `/v1/models`) to SageMaker TGI `invoke_endpoint()` calls
- **Auth**: SigV4-signed calls to SageMaker (IAM role with `sagemaker:InvokeEndpoint` only)

### API Gateway v2
- **Type**: HTTP API (not REST API)
- **Routes**: `POST /v1/chat/completions`, `POST /v1/completions`, `GET /v1/models`
- **CORS**: Allow all origins, GET/POST/OPTIONS
- **Integration**: AWS_PROXY to Lambda (payload format 2.0)

### ECS Fargate (OpenWebUI)
- **Image**: `ghcr.io/open-webui/open-webui:main`
- **Resources**: 512 CPU (0.5 vCPU) / 1024 MB memory
- **Port**: 8080 (container) exposed via ALB on port 80
- **Config**: `OPENAI_API_BASE_URL` points to API Gateway, auth disabled, Ollama disabled
- **Logs**: CloudWatch `/ecs/<stack>/openwebui`, 7-day retention

### Application Load Balancer
- **Scheme**: Internet-facing
- **Subnets**: 2 public subnets in different AZs (required)
- **Health check**: `GET /` on port 8080, 30s interval
- **Security**: ALB SG allows inbound port 80; Fargate SG allows port 8080 from ALB SG only

### IAM Roles (3)
- **SageMaker**: `AmazonSageMakerFullAccess` + ECR pull
- **Lambda**: `AWSLambdaBasicExecutionRole` + `sagemaker:InvokeEndpoint`
- **ECS Task Execution**: `AmazonECSTaskExecutionRolePolicy` (ECR pull + CloudWatch Logs)

## Data Flow

1. **Browser** hits ALB on port 80
2. **ALB** forwards to Fargate task (OpenWebUI) on port 8080
3. **OpenWebUI** sends OpenAI-format requests to **API Gateway**
4. **API Gateway** proxies to **Lambda**
5. **Lambda** translates to TGI format, calls `sagemaker:InvokeEndpoint` (SigV4-signed)
6. **SageMaker TGI** runs inference on GPU, returns generated text
7. **Lambda** formats response as OpenAI chat completion, returns to client

## Cost

| Resource | Cost/Hour |
|----------|-----------|
| SageMaker ml.g5.xlarge | ~$1.41 |
| Fargate (0.5 vCPU / 1 GB) | ~$0.03 |
| ALB | ~$0.02 |
| API Gateway | ~$1/million requests |
| **Total** | **~$1.46/hour** |

## Diagram Source

Editable diagram: [architecture.drawio](architecture.drawio) (open with [app.diagrams.net](https://app.diagrams.net))
