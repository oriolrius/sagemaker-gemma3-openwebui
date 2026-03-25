# infra/

CloudFormation IaC and deployment scripts.

## Files

- `full-stack.yaml` — Single CloudFormation template (up to 23 resources; 22 when using external SageMaker role)
- `deploy-full-stack.sh` — Orchestrates: package Lambda -> create S3 -> upload -> deploy CFN -> show outputs
- `delete-full-stack.sh` — Deletes stack + S3 bucket

## CloudFormation Parameters

Required: `VpcId`, `SubnetId`, `SubnetId2` (2 public subnets in different AZs for ALB), `LambdaS3Bucket`, `LambdaS3Key`.
Optional: `HuggingFaceModelId` (default: `oriolrius/myemoji-gemma-3-270m-it`), `SageMakerInstanceType` (default: `ml.g5.xlarge`).

## Resources Created

- **SageMaker**: Model, EndpointConfig, Endpoint (TGI container: `huggingface-pytorch-tgi-inference:2.7.0-tgi3.3.6-gpu-py311-cu124`)
- **Lambda**: Function (Python 3.11, 60s timeout, 256MB) + IAM role (sagemaker:InvokeEndpoint only)
- **API Gateway v2**: HTTP API + 3 routes (`POST /v1/chat/completions`, `POST /v1/completions`, `GET /v1/models`)
- **ECS Fargate**: Cluster, TaskDef (512 CPU/1024 MB), Service, ALB, TargetGroup, Listener, 2 SecurityGroups, LogGroup
- **IAM**: SageMaker role, Lambda role, ECS task execution role (trusts `ecs-tasks.amazonaws.com`)

## Deploy

```bash
./deploy-full-stack.sh --vpc-id vpc-xxx --subnet-id subnet-xxx --subnet-id-2 subnet-yyy
# Optional: --stack-name, --model-id, --sagemaker-instance
```

## TGI Environment

```yaml
HF_MODEL_ID: oriolrius/myemoji-gemma-3-270m-it
SM_NUM_GPUS: '1'
MAX_INPUT_TOKENS: '1024'
MAX_TOTAL_TOKENS: '2048'
DTYPE: bfloat16
MAX_CONCURRENT_REQUESTS: '4'
```
