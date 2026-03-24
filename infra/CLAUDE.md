# infra/

CloudFormation IaC and deployment scripts. EC2-based architecture (v1.x).

## Files

- `full-stack.yaml` — Single CloudFormation template
- `deploy-full-stack.sh` — Orchestrates: package Lambda -> create S3 -> upload OpenWebUI files -> deploy CFN
- `delete-full-stack.sh` — Deletes stack + S3 bucket

## CloudFormation Parameters

Required: `VpcId`, `SubnetId` (1 public subnet), `LambdaS3Bucket`, `LambdaS3Key`.
Optional: `HuggingFaceModelId` (default: `oriolrius/myemoji-gemma-3-270m-it`), `SageMakerInstanceType` (default: `ml.g5.xlarge`), `EC2InstanceType` (default: `t3.small`), `EC2KeyPair`, `AllowedSSHCidr`.

## Resources Created

- **SageMaker**: Model, EndpointConfig, Endpoint (TGI `huggingface-pytorch-tgi-inference:2.7.0-tgi3.3.6-gpu-py311-cu124`)
- **Lambda**: Function (Python 3.11, 60s timeout, 256MB) + IAM role
- **API Gateway v2**: HTTP API + 3 routes (`/v1/chat/completions`, `/v1/completions`, `/v1/models`)
- **EC2**: Instance (Docker + OpenWebUI), Security Group (HTTP/HTTPS/SSH), IAM Role/InstanceProfile, Elastic IP
- **IAM**: SageMaker role, Lambda role, EC2 role (SSM + S3 read)

## Deploy

```bash
./deploy-full-stack.sh --vpc-id vpc-xxx --subnet-id subnet-xxx
# Optional: --key-pair, --ec2-instance, --model-id, --sagemaker-instance
```
