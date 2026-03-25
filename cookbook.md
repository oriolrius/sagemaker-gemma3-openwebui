# Cookbook: Deploy a Language Model on AWS with SageMaker

This guide walks through deploying a HuggingFace language model on AWS SageMaker with a public OpenAI-compatible API and a web-based chat interface (OpenWebUI). Every step includes verification checkpoints so you know the process is on track before moving forward.

**What you will build:**

```
Browser --> OpenWebUI (Fargate/ALB) --> API Gateway --> Lambda --> SageMaker TGI Endpoint (GPU)
```

**Time required:** ~25-30 minutes (most of it is waiting for SageMaker)

**Cost:** ~$1.46/hour while running. You must delete all resources when done.

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Clone the Repository](#2-clone-the-repository)
3. [Configure AWS Credentials](#3-configure-aws-credentials)
4. [Check GPU Quota](#4-check-gpu-quota)
5. [Find Your VPC and Subnet](#5-find-your-vpc-and-subnet)
6. [Run the Lambda Tests](#6-run-the-lambda-tests)
7. [Deploy the Full Stack](#7-deploy-the-full-stack)
8. [Monitor the Deployment](#8-monitor-the-deployment)
9. [Test the API](#9-test-the-api)
10. [Use the Web Chat Interface](#10-use-the-web-chat-interface)
11. [Cleanup (Required)](#11-cleanup-required)
12. [Verify Cleanup](#12-verify-cleanup)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. Prerequisites

Before starting, make sure these tools are installed and working.

### Required Software

| Tool | Purpose | Install |
|------|---------|---------|
| **AWS CLI v2** | Interact with AWS services | [Install guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) |
| **Git** | Clone the repository | `sudo apt install git` or [git-scm.com](https://git-scm.com/) |
| **uv** | Python package manager | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| **curl** | Test API endpoints | Pre-installed on most systems |
| **zip** | Package Lambda function | `sudo apt install zip` |

### Verify Each Tool

Run all of these and confirm they produce output (not "command not found"):

```bash
aws --version
git --version
uv --version
curl --version
zip --version
```

### Checkpoint

All five commands return version numbers. If any command fails, install that tool before continuing.

---

## 2. Clone the Repository

Clone this repository and navigate into it. **All commands in this guide are run from the repository root** unless stated otherwise.

```bash
git clone https://github.com/oriolrius/sagemaker-gemma3-openwebui.git
cd sagemaker-gemma3-openwebui
```

### Checkpoint

```bash
ls infra/full-stack.yaml
```

This file exists. If not, you are in the wrong directory.

---

## 3. Configure AWS Credentials

AWS CLI needs valid credentials to create resources. These credentials come from your AWS account (typically via AWS SSO or an Innovation Sandbox portal).

### Option A: Environment Variables (Recommended for Sandbox/Temporary Credentials)

If you received `export` commands from a sandbox portal or credential provider, paste them directly into your terminal:

```bash
export AWS_ACCESS_KEY_ID="ASIA..."
export AWS_SECRET_ACCESS_KEY="..."
export AWS_SESSION_TOKEN="..."
export AWS_DEFAULT_REGION="eu-west-1"
```

These are valid only for the current terminal session. If you close the terminal, you need to set them again.

### Option B: AWS CLI Configuration (Persistent)

If you have an AWS Access Key ID, Secret Access Key, and Session Token and want them saved to disk:

```bash
aws configure set aws_access_key_id <YOUR_ACCESS_KEY_ID>
aws configure set aws_secret_access_key <YOUR_SECRET_ACCESS_KEY>
aws configure set aws_session_token <YOUR_SESSION_TOKEN>
aws configure set region eu-west-1
```

This writes to `~/.aws/credentials` and persists across terminal sessions.

### Option C: AWS SSO Login

If your organization uses AWS SSO (Identity Center):

```bash
aws configure sso
# Follow the prompts: SSO start URL, region, account, role
```

### Verify Credentials

```bash
aws sts get-caller-identity
```

**Expected output:**

```json
{
    "UserId": "AROA...:your-session-name",
    "Account": "123456789012",
    "Arn": "arn:aws:sts::123456789012:assumed-role/..."
}
```

### Checkpoint

- The `get-caller-identity` command returns your Account ID (a 12-digit number)
- The region is set to `eu-west-1` (verify with `aws configure get region` or `echo $AWS_DEFAULT_REGION`)
- Write down your **Account ID** -- you will need it later

### If This Fails

| Error | Cause | Fix |
|-------|-------|-----|
| `Unable to locate credentials` | No credentials configured | Set environment variables (Option A) or run `aws configure` |
| `ExpiredTokenException` | Session token has expired | Get fresh credentials from your SSO portal |
| `InvalidClientTokenId` | Wrong access key | Double-check the access key ID is correct |

---

## 4. Check GPU Quota

SageMaker requires a GPU instance to run HuggingFace TGI. Your AWS account must have quota for at least 1 `ml.g5.xlarge` instance in `eu-west-1`. New accounts often have a quota of 0 for GPU instances. The default model (Gemma 3) requires bfloat16 support, which is available on A10G GPUs (g5 instances) but not on T4 GPUs (g4dn instances).

### Check via AWS CLI

```bash
aws service-quotas list-service-quotas \
  --service-code sagemaker \
  --region eu-west-1 \
  --query "Quotas[?contains(QuotaName, 'ml.g5.xlarge') && contains(QuotaName, 'endpoint')].[QuotaName,Value]" \
  --output table
```

**Expected output:**

```
---------------------------------------------------
| ml.g5.xlarge for endpoint usage |  1.0        |
---------------------------------------------------
```

### Check via AWS Console

1. Open the [Service Quotas console for SageMaker in eu-west-1](https://eu-west-1.console.aws.amazon.com/servicequotas/home/services/sagemaker/quotas)
2. In the search box, type `ml.g5.xlarge`
3. Find the row **"ml.g5.xlarge for endpoint usage"**
4. Check the **Applied quota value** column

### Checkpoint

- The quota value is **1** or higher
- If the quota is **0**, you must request an increase before continuing (see below)

### Request a Quota Increase (if quota is 0)

If your quota is 0, you **must** request an increase before deploying. Here is the exact process:

#### Via AWS Console (Recommended)

1. Open the [Service Quotas console for SageMaker in eu-west-1](https://eu-west-1.console.aws.amazon.com/servicequotas/home/services/sagemaker/quotas)
2. In the **search box**, type: `ml.g5.xlarge`
3. Click on the quota name: **"ml.g5.xlarge for endpoint usage"**
4. On the quota detail page, you will see:
   - **Applied quota value**: `0` (your current limit)
   - **AWS default quota value**: the default for this region
5. Click the **"Request increase at account level"** button (orange button, top-right area)
6. In the **"Increase quota value"** field, enter: `1`
7. Click **"Request"**
8. You will see a confirmation banner: *"Quota increase request submitted"*

#### Via AWS CLI

```bash
# Get the quota code first
QUOTA_CODE=$(aws service-quotas list-service-quotas \
  --service-code sagemaker \
  --region eu-west-1 \
  --query "Quotas[?contains(QuotaName, 'ml.g5.xlarge') && contains(QuotaName, 'endpoint')].QuotaCode" \
  --output text)

# Request the increase
aws service-quotas request-service-quota-increase \
  --service-code sagemaker \
  --quota-code "$QUOTA_CODE" \
  --desired-value 1 \
  --region eu-west-1
```

#### Check Request Status

Monitor the status of your request:

```bash
aws service-quotas list-requested-service-quota-change-history \
  --service-code sagemaker \
  --region eu-west-1 \
  --query "RequestedQuotas[?contains(QuotaName, 'g5.xlarge')].[QuotaName,Status,DesiredValue]" \
  --output table
```

Or in the console: [Service Quotas > Quota request history](https://eu-west-1.console.aws.amazon.com/servicequotas/home/requests)

| Status | Meaning |
|--------|---------|
| `PENDING` | AWS is reviewing your request |
| `CASE_OPENED` | A support case was created -- check your email |
| `APPROVED` | Quota increased -- you can proceed with deployment |
| `DENIED` | Request denied -- contact AWS Support with a business justification |

#### Expected Wait Time

- **Sandbox/Lab accounts**: Often approved automatically within minutes to a few hours
- **New production accounts**: 1-3 business days
- **Large increases (>4 instances)**: May require a support case with justification

**You cannot proceed with the deployment until the quota is at least 1.** Re-run the quota check command from above to verify after approval.

---

## 5. Find Your VPC and Subnet

The Fargate service and ALB (which run OpenWebUI) need a VPC with **two public subnets in different Availability Zones**.

### What Are VPCs and Subnets?

- **VPC (Virtual Private Cloud)**: An isolated virtual network in your AWS account
- **Subnet**: A range of IP addresses within a VPC
- **Internet Gateway (IGW)**: Enables internet access for resources in a VPC
- **ALB requirement**: Application Load Balancers require subnets in at least 2 different AZs
- The key requirement is that the subnets' **route table** has a route to an Internet Gateway (`0.0.0.0/0` → `igw-xxx`)

### Find VPC via CLI

```bash
aws ec2 describe-vpcs --region eu-west-1 \
  --query 'Vpcs[*].{ID:VpcId,Name:Tags[?Key==`Name`].Value|[0],CIDR:CidrBlock,Default:IsDefault}' \
  --output table
```

**Example output (default VPC):**

```
-------------------------------------------------------------
|                        DescribeVpcs                       |
+----------------+--------+-----------------------+---------+
|      CIDR      | Default|          ID           |  Name   |
+----------------+--------+-----------------------+---------+
|  172.31.0.0/16 |  True  |  vpc-0abc123def456789 |  None   |
+----------------+--------+-----------------------+---------+
```

**Example output (no default VPC — custom VPC only):**

```
-------------------------------------------------------------
|                        DescribeVpcs                       |
+----------------+--------+-----------------------+------------------+
|      CIDR      | Default|          ID           |      Name        |
+----------------+--------+-----------------------+------------------+
|  10.0.0.0/16   |  False |  vpc-0585686b45f950687|  sagemaker-vpc   |
+----------------+--------+-----------------------+------------------+
```

Write down the **VPC ID**. If you have a default VPC (`Default: True`), use that one. Otherwise, use whatever VPC is available.

### Find a Subnet with Internet Access

Replace `<your-vpc-id>` with the VPC ID from the previous step:

```bash
aws ec2 describe-subnets --region eu-west-1 \
  --filters "Name=vpc-id,Values=<your-vpc-id>" \
  --query 'Subnets[*].{ID:SubnetId,AZ:AvailabilityZone,CIDR:CidrBlock,AutoPublicIP:MapPublicIpOnLaunch}' \
  --output table
```

**Example output:**

```
-----------------------------------------------------------------------
|                           DescribeSubnets                           |
+---------------+--------------+----------------------------+---------+
| AutoPublicIP  |     AZ       |            ID              |  CIDR   |
+---------------+--------------+----------------------------+---------+
|  True         | eu-west-1a   | subnet-0aaa111bbb          | 172...  |
|  True         | eu-west-1b   | subnet-0bbb222ccc          | 172...  |
+---------------+--------------+----------------------------+---------+
```

Write down **two Subnet IDs in different AZs** (e.g., one in `eu-west-1a` and one in `eu-west-1b`). The ALB requires subnets in at least 2 AZs. If you only have one subnet, create a second one in a different AZ.

### Verify the Subnet Has Internet Access

This is the critical check — the subnet must have a route to an Internet Gateway:

```bash
# Check if an Internet Gateway is attached to your VPC
aws ec2 describe-internet-gateways --region eu-west-1 \
  --filters "Name=attachment.vpc-id,Values=<your-vpc-id>" \
  --query 'InternetGateways[*].InternetGatewayId' --output text
```

If this returns an IGW ID (e.g., `igw-0b7276cca4bd4097a`), your VPC has internet access. If it returns nothing, your VPC cannot reach the internet — see [If No Internet Gateway](#if-no-internet-gateway) below.

### Find VPC and Subnet via AWS Console

1. Open the [VPC Console in eu-west-1](https://eu-west-1.console.aws.amazon.com/vpc/home?region=eu-west-1#vpcs:)
2. Pick a VPC — use the **Default VPC** (if one exists) or any other VPC
3. Copy the **VPC ID**
4. In the left sidebar, click **Subnets** ([direct link](https://eu-west-1.console.aws.amazon.com/vpc/home?region=eu-west-1#subnets:))
5. Filter by your VPC ID
6. Copy **any Subnet ID** from the list
7. Verify internet access: click **Internet Gateways** in the left sidebar and confirm one is attached to your VPC

### Checkpoint

You now have two values written down:

| Value | Example | Your Value |
|-------|---------|------------|
| VPC ID | `vpc-0abc123def456789` | _____________ |
| Subnet ID 1 | `subnet-0aaa111bbb` (eu-west-1a) | _____________ |
| Subnet ID 2 | `subnet-0ccc333ddd` (eu-west-1b) | _____________ |

All three values are required for the next steps. You have also confirmed that an Internet Gateway is attached to your VPC.

### If No Internet Gateway

Your VPC has no internet access. This is uncommon — default VPCs always have one. If you are using a custom VPC without an IGW:

1. Go to **VPC Console** > **Internet Gateways** > **Create internet gateway**
2. Select the new IGW > **Actions** > **Attach to VPC** > select your VPC
3. Go to **Route Tables** > select the route table associated with your subnet
4. **Edit routes** > add a route: Destination `0.0.0.0/0`, Target: your new IGW
5. Re-run the verify command above to confirm

---

## 6. Run the Lambda Tests

Before deploying to AWS, verify the Lambda proxy code works correctly. Run from the repository root:

```bash
cd lambda/openai-proxy
uv sync --dev
uv run pytest -v
```

**Expected output:**

```
tests/test_handler.py::TestCreateResponse::test_basic_response PASSED
tests/test_handler.py::TestCreateResponse::test_custom_headers PASSED
...
============================== 19 passed in 0.13s ==============================
```

### Checkpoint

- All 19 tests pass
- No test failures or errors

### If Tests Fail

| Error | Fix |
|-------|-----|
| `uv: command not found` | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` then restart your terminal |
| `ModuleNotFoundError` | Run `uv sync --dev` again |
| Test assertion errors | Check that you haven't modified `handler.py` -- run `git checkout lambda/openai-proxy/src/` to reset |

Return to the repository root when done:

```bash
cd ../..
```

---

## 7. Deploy the Full Stack

This step packages the Lambda function, uploads it to S3, and deploys all AWS resources via CloudFormation.

### Run the Deploy Script

Replace the placeholders with your actual values from Step 5:

```bash
cd infra/

./deploy-full-stack.sh \
  --vpc-id <your-vpc-id> \
  --subnet-id <your-subnet-id-1> \
  --subnet-id-2 <your-subnet-id-2>
```

**Example with real values:**

```bash
./deploy-full-stack.sh \
  --vpc-id vpc-0abc123def456789 \
  --subnet-id subnet-0aaa111bbb \
  --subnet-id-2 subnet-0ccc333ddd
```

The script will:

1. Show a summary of what will be created
2. Ask for confirmation (`Continue? [y/N]`) -- press **y** (no Enter needed)
3. Package the Lambda function (~30 seconds)
4. Create an S3 bucket and upload files (~30 seconds)
5. Deploy the CloudFormation stack (~15-20 minutes)
6. Display the endpoints when complete

### What Gets Created

| Resource | Type | Purpose |
|----------|------|---------|
| SageMaker Model | ML Model | TGI container configuration |
| SageMaker Endpoint Config | Config | Instance type and variant settings |
| SageMaker Endpoint | **GPU Instance** | Runs the language model (ml.g5.xlarge) |
| Lambda Function | Compute | Translates OpenAI API format to SageMaker format |
| API Gateway HTTP API | Public API | Exposes the Lambda function at a public URL |
| ECS Fargate Service | Container | Runs the OpenWebUI chat interface |
| Application Load Balancer | Load Balancer | Routes HTTP traffic to Fargate tasks |
| ECS Cluster | Orchestration | Manages Fargate tasks |
| 3 IAM Roles | Security | Least-privilege permissions for each service |
| 2 Security Groups | Firewall | ALB (port 80 public) + Fargate (port 8080 from ALB) |
| S3 Bucket | Storage | Lambda deployment package |

### Checkpoint

The script finishes with output similar to:

```
============================================
Deployment Complete!
============================================

SageMaker Endpoint: openai-sagemaker-stack-vllm-endpoint
API Gateway:        https://abc123xyz.execute-api.eu-west-1.amazonaws.com
OpenWebUI:          http://openai-sagemaker-stack-alb-123456.eu-west-1.elb.amazonaws.com
```

Write down these values:

| Value | Your Value |
|-------|------------|
| API Gateway URL | _________________________ |
| OpenWebUI URL (ALB) | _________________________ |
| SageMaker Endpoint Name | _________________________ |

### If the Script Fails Before CloudFormation

| Error | Cause | Fix |
|-------|-------|-----|
| `ERROR: --vpc-id is required` | Missing argument | Add `--vpc-id` with your VPC ID |
| `ExpiredTokenException` | AWS credentials expired | Refresh credentials (Step 3), then re-run |
| `zip: command not found` | zip not installed | `sudo apt install zip` |
| `uv: command not found` | uv not installed | See Step 1 prerequisites |

---

## 8. Monitor the Deployment

The CloudFormation deployment takes 15-20 minutes. Most of that time is SageMaker provisioning the GPU instance and loading the model. You can monitor progress in real-time.

### Monitor via CLI

Watch CloudFormation events in your terminal:

```bash
# Using watch (Linux)
watch -n 10 "aws cloudformation describe-stack-events \
  --stack-name openai-sagemaker-stack \
  --region eu-west-1 \
  --query 'StackEvents[0:5].[Timestamp,LogicalResourceId,ResourceStatus]' \
  --output table"

# If watch is not available (macOS), run manually and repeat:
aws cloudformation describe-stack-events \
  --stack-name openai-sagemaker-stack \
  --region eu-west-1 \
  --query 'StackEvents[0:5].[Timestamp,LogicalResourceId,ResourceStatus]' \
  --output table
```

Press `Ctrl+C` to stop watching (if using `watch`).

### Monitor via AWS Console

1. Open the [CloudFormation console in eu-west-1](https://eu-west-1.console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks)
2. Click your stack name (**openai-sagemaker-stack**)
3. Click the **Events** tab
4. The page auto-refreshes. Watch for resources transitioning from `CREATE_IN_PROGRESS` to `CREATE_COMPLETE`

### What to Expect (Timeline)

| Time | What Happens |
|------|-------------|
| 0-1 min | IAM roles created |
| 1-2 min | API Gateway, Security Group created |
| 2-3 min | SageMaker Model and Endpoint Config created |
| 3-5 min | Lambda function created, ECS Fargate service starting |
| 5-20 min | **SageMaker Endpoint: Creating** (pulls container image, downloads model, loads into GPU) |
| 15-20 min | SageMaker Endpoint transitions to **InService** |
| 20 min | Stack status: **CREATE_COMPLETE** |

### Check SageMaker Endpoint Status Separately

The SageMaker endpoint is the slowest resource. To check its status directly:

```bash
aws sagemaker describe-endpoint \
  --endpoint-name openai-sagemaker-stack-vllm-endpoint \
  --region eu-west-1 \
  --query 'EndpointStatus'
```

| Status | Meaning |
|--------|---------|
| `Creating` | Still provisioning -- wait |
| `InService` | Ready to accept requests |
| `Failed` | Something went wrong -- see [Troubleshooting](#13-troubleshooting) |

You can also check the endpoint in the [SageMaker Console > Inference > Endpoints](https://eu-west-1.console.aws.amazon.com/sagemaker/home?region=eu-west-1#/endpoints).

### Checkpoint

- CloudFormation stack status is **CREATE_COMPLETE**
- SageMaker endpoint status is **InService**

### If the Stack Fails (ROLLBACK_IN_PROGRESS)

Find the root cause by looking for the first `CREATE_FAILED` event:

```bash
aws cloudformation describe-stack-events \
  --stack-name openai-sagemaker-stack \
  --region eu-west-1 \
  --query "StackEvents[?ResourceStatus=='CREATE_FAILED'].[LogicalResourceId,ResourceStatusReason]" \
  --output table
```

Common failures and fixes:

| Failed Resource | Error Message | Fix |
|-----------------|---------------|-----|
| SageMakerEndpoint | `ResourceLimitExceeded` | GPU quota is 0 -- request increase (Step 4) |
| LambdaFunction | `S3 error: Access Denied` | S3 bucket region mismatch -- re-run deploy script |
| Any IAM resource | `Requires capabilities` | Missing `--capabilities` flag -- the deploy script includes this automatically |

After fixing the issue, delete the failed stack and redeploy:

```bash
aws cloudformation delete-stack --stack-name openai-sagemaker-stack --region eu-west-1
aws cloudformation wait stack-delete-complete --stack-name openai-sagemaker-stack --region eu-west-1
# Then re-run the deploy script
```

---

## 9. Test the API

Once the stack is deployed and the SageMaker endpoint is `InService`, test the API.

### Test 1: List Available Models

Replace `<api-gateway-url>` with your API Gateway URL from Step 7:

```bash
curl <api-gateway-url>/v1/models
```

**Expected output:**

```json
{
  "object": "list",
  "data": [
    {
      "id": "openai-sagemaker-stack-vllm-endpoint",
      "object": "model",
      "created": 1677610602,
      "owned_by": "sagemaker"
    }
  ]
}
```

### Test 2: Send a Chat Completion Request

```bash
curl -X POST <api-gateway-url>/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "The future of artificial intelligence is"}],
    "max_tokens": 50,
    "temperature": 0.7
  }'
```

**Expected output:**

```json
{
  "id": "chatcmpl-...",
  "object": "chat.completion",
  "model": "openai-sagemaker-stack-vllm-endpoint",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "...generated text continues here..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 7,
    "completion_tokens": 50,
    "total_tokens": 57
  }
}
```

### Understanding the Response

The default model is **oriolrius/myemoji-gemma-3-270m-it**, a Gemma 3 270M instruction-tuned model. Being instruction-tuned, it responds naturally to conversational prompts:

| Prompt Style | Works? | Example |
|-------------|--------|---------|
| Direct question | Yes | `"What is AI?"` --> produces a coherent answer |
| Chat conversation | Yes | Multi-turn conversations work naturally |
| Text completion | Yes | `"The capital of France is"` --> `"Paris, the city of..."` |

If you need more capable responses, deploy a larger model like `google/gemma-3-1b-it` (fits on ml.g5.xlarge with 24 GB GPU memory).

### Checkpoint

- `/v1/models` returns a JSON list with your endpoint name
- `/v1/chat/completions` returns generated text in the `choices[0].message.content` field
- Both requests complete within ~30 seconds

### If the API Returns Errors

| HTTP Status | Error | Fix |
|-------------|-------|-----|
| 500 | `"SageMaker error"` | Endpoint may not be ready -- check: `aws sagemaker describe-endpoint --endpoint-name openai-sagemaker-stack-vllm-endpoint --query EndpointStatus` |
| 504 | Gateway Timeout | Request took too long -- try again (first request after deployment can be slow) |
| 403 | Forbidden | API Gateway URL is wrong -- check the CloudFormation outputs |
| Connection refused | Nothing listening | Verify the API Gateway was created: `aws apigatewayv2 get-apis --region eu-west-1` |

---

## 10. Use the Web Chat Interface

OpenWebUI provides a web-based chat interface similar to ChatGPT, connected to your SageMaker model via the API Gateway.

### Access OpenWebUI

Open your browser and navigate to the OpenWebUI URL from Step 7:

```
http://<alb-dns-name>
```

**Important:** Use `http://` (not `https://`). The ALB DNS name looks like `openai-sagemaker-stack-alb-123456.eu-west-1.elb.amazonaws.com`.

### First-Time Setup

1. The OpenWebUI interface loads in your browser
2. Authentication is **disabled** in this setup, so you may go directly to the chat interface
3. If prompted to create an account, enter any email/password -- this is stored in the Fargate task (ephemeral)
4. The model **openai-sagemaker-stack-vllm-endpoint** should appear in the model selector

### Send a Message

1. Select the model from the dropdown (if not already selected)
2. Type a text completion prompt like: `The most important invention in human history is`
3. Press Enter or click Send
4. The response appears after a few seconds

### Checkpoint

- The OpenWebUI page loads in your browser
- You can select the SageMaker model
- Sending a message returns generated text

### If OpenWebUI Does Not Load

The Fargate task takes 2-3 minutes after the stack completes to pull the Docker image and pass ALB health checks. Wait a few minutes and try again.

**Check ECS service status:**

```bash
aws ecs describe-services \
  --cluster openai-sagemaker-stack-cluster \
  --services openai-sagemaker-stack-openwebui \
  --region eu-west-1 \
  --query 'services[0].{status:status,running:runningCount,desired:desiredCount}'
```

**Check Fargate task logs:**

```bash
aws logs tail /ecs/openai-sagemaker-stack/openwebui --follow --region eu-west-1
```

Or in the [ECS Console](https://eu-west-1.console.aws.amazon.com/ecs/v2/clusters) > click your cluster > Services > Tasks > Logs.

---

## 11. Cleanup (Required)

**This stack costs ~$1.46/hour (~$35/day)**. The SageMaker GPU instance (ml.g5.xlarge) is the primary cost driver. Always delete all resources when you are done.

### Delete via Script

```bash
cd infra/
./delete-full-stack.sh --stack-name openai-sagemaker-stack --region eu-west-1
```

The script will:
1. Show what will be deleted
2. Ask for confirmation -- press **y** to confirm
3. Delete the CloudFormation stack (5-10 minutes)
4. Delete the S3 bucket
5. Confirm cleanup is complete

### Delete via AWS Console

1. Open the [CloudFormation console](https://eu-west-1.console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks)
2. Select your stack (**openai-sagemaker-stack**)
3. Click **Delete**
4. Confirm the deletion
5. Wait for the stack status to show **DELETE_COMPLETE** (5-10 minutes)

Then delete the S3 bucket manually:

```bash
# Find the bucket name
aws s3 ls | grep openai-sagemaker-stack

# Empty and delete it
aws s3 rb s3://<bucket-name> --force --region eu-west-1
```

### Checkpoint

- The CloudFormation stack is deleted or shows **DELETE_COMPLETE**
- The S3 bucket no longer exists

---

## 12. Verify Cleanup

Confirm that no billable resources remain. Run each of these commands and verify they return empty results.

### CloudFormation Stack

```bash
aws cloudformation describe-stacks --region eu-west-1 \
  --stack-name openai-sagemaker-stack 2>&1
```

**Expected:** `Stack with id openai-sagemaker-stack does not exist`

### SageMaker Endpoints

```bash
aws sagemaker list-endpoints --region eu-west-1 \
  --query 'Endpoints[?contains(EndpointName, `openai-sagemaker-stack`)]'
```

**Expected:** `[]` (empty array)

### Lambda Functions

```bash
aws lambda list-functions --region eu-west-1 \
  --query 'Functions[?contains(FunctionName, `openai-sagemaker-stack`)]'
```

**Expected:** `[]` (empty array)

### ECS Services

```bash
aws ecs list-services --cluster openai-sagemaker-stack-cluster --region eu-west-1 2>&1
```

**Expected:** `ClusterNotFoundException` (cluster deleted) or empty list

### API Gateways

```bash
aws apigatewayv2 get-apis --region eu-west-1 \
  --query 'Items[?contains(Name, `openai-sagemaker-stack`)]'
```

**Expected:** `[]` (empty array)

### Checkpoint

All five commands return empty results. **No ongoing charges.**

---

## 13. Troubleshooting

### Quick Diagnostic Reference

| Symptom | First Command to Run |
|---------|---------------------|
| Stack failing to create | `aws cloudformation describe-stack-events --stack-name openai-sagemaker-stack --query "StackEvents[?ResourceStatus=='CREATE_FAILED'].[LogicalResourceId,ResourceStatusReason]" --output table` |
| SageMaker endpoint not working | `aws sagemaker describe-endpoint --endpoint-name openai-sagemaker-stack-vllm-endpoint --query '[EndpointStatus,FailureReason]'` |
| SageMaker container errors | `aws logs tail /aws/sagemaker/Endpoints/openai-sagemaker-stack-vllm-endpoint --follow` |
| Lambda returning 500 errors | `aws logs filter-log-events --log-group-name /aws/lambda/openai-sagemaker-stack-openai-proxy --filter-pattern "ERROR"` |
| Any AWS error | `aws sts get-caller-identity` (check credentials first) |

---

### Credential Issues

#### ExpiredTokenException

```
An error occurred (ExpiredTokenException) when calling the ... operation:
The security token included in the request is expired
```

**Cause:** AWS session tokens from Innovation Sandbox or SSO expire after 1-12 hours.

**Fix:** Obtain fresh credentials from your AWS portal and reconfigure:

```bash
aws configure set aws_access_key_id <NEW_KEY>
aws configure set aws_secret_access_key <NEW_SECRET>
aws configure set aws_session_token <NEW_TOKEN>
aws sts get-caller-identity  # verify the new credentials work
```

#### AccessDeniedException

```
User: arn:aws:sts::123456789012:assumed-role/... is not authorized to perform: ...
```

**Cause:** Your IAM role lacks the required permission. The error message tells you exactly which permission is missing.

**Fix:** Use a role with broader permissions (e.g., `AdministratorAccess` for sandbox environments) or ask your administrator to add the specific permission.

#### Region Mismatch

```
Could not resolve endpoint / Endpoint ... not found
```

**Cause:** The AWS CLI is configured for a different region than where your resources exist.

**Fix:** Always specify `--region eu-west-1` in commands, or set:

```bash
export AWS_DEFAULT_REGION=eu-west-1
```

---

### SageMaker Errors

#### ResourceLimitExceeded (Quota)

```
The account-level service limit 'ml.g5.xlarge for endpoint usage' is 0 Instances
```

**Cause:** Your account has zero quota for this GPU instance type.

**Fix:** Request a quota increase (Step 4). You cannot deploy until the quota is at least 1.

#### CUDA Out of Memory

Visible in CloudWatch logs (`/aws/sagemaker/Endpoints/<endpoint-name>`):

```
torch.cuda.OutOfMemoryError: CUDA out of memory
```

**Cause:** The model is too large for the GPU memory (24 GB on ml.g5.xlarge with A10G GPU).

**Fix:** Use a smaller model. The default Gemma 3 270M fits easily. Models larger than ~7B parameters in bfloat16 will not fit on a single A10G GPU.

#### Endpoint Stuck in "Creating"

**Cause:** Model download or container startup is slow. Normal for first deployment.

**Fix:** Wait up to 25 minutes. If still stuck, check CloudWatch logs:

```bash
aws logs tail /aws/sagemaker/Endpoints/openai-sagemaker-stack-vllm-endpoint --follow
```

If no logs appear at all after 10 minutes, the container failed to start. Check the IAM role has ECR permissions.

---

### CloudFormation Errors

#### ROLLBACK_IN_PROGRESS

**Cause:** One resource failed, triggering automatic rollback of all resources.

**Fix:** Find the root cause (the first `CREATE_FAILED` event):

```bash
aws cloudformation describe-stack-events \
  --stack-name openai-sagemaker-stack \
  --query "StackEvents[?ResourceStatus=='CREATE_FAILED'].[LogicalResourceId,ResourceStatusReason]" \
  --output table
```

After the rollback completes (`ROLLBACK_COMPLETE`), fix the underlying issue and deploy again. The failed stack remains in `ROLLBACK_COMPLETE` state -- delete it first:

```bash
aws cloudformation delete-stack --stack-name openai-sagemaker-stack --region eu-west-1
aws cloudformation wait stack-delete-complete --stack-name openai-sagemaker-stack --region eu-west-1
```

Then re-run the deploy script.

#### Stack Deletion Fails

```
DELETE_FAILED: The bucket you tried to delete is not empty
```

**Fix:** Empty the S3 bucket first, then retry:

```bash
aws s3 rm s3://<bucket-name> --recursive
aws cloudformation delete-stack --stack-name openai-sagemaker-stack --region eu-west-1
```

---

### API Gateway / Lambda Errors

#### 504 Gateway Timeout

**Cause:** API Gateway has a 29-second hard timeout for HTTP APIs. If SageMaker takes longer to respond (common on cold start), the request times out.

**Fix:** Retry the request. The first request after deployment is the slowest because the model needs a "warm-up" inference. Subsequent requests should complete in 5-15 seconds.

#### Internal Server Error (500)

**Cause:** Lambda function threw an unhandled exception.

**Fix:** Check Lambda logs:

```bash
aws logs tail /aws/lambda/openai-sagemaker-stack-openai-proxy --since 5m
```

Or in the [Lambda Console](https://eu-west-1.console.aws.amazon.com/lambda/home?region=eu-west-1#/functions) > click your function > **Monitor** tab > **View CloudWatch logs**.

---

### ECS / OpenWebUI Errors

#### OpenWebUI Page Does Not Load

**Causes (in order of likelihood):**

1. **Fargate task still starting** -- wait 2-3 minutes after stack completion for image pull + health checks
2. **Task failed to start** -- check ECS service events and task logs
3. **ALB security group issue** -- verify ALB security group allows inbound port 80

**Check Fargate task status:**

```bash
# Check service status
aws ecs describe-services --cluster openai-sagemaker-stack-cluster \
  --services openai-sagemaker-stack-openwebui --region eu-west-1 \
  --query 'services[0].{running:runningCount,desired:desiredCount,events:events[0:3]}'

# Check task logs
aws logs tail /ecs/openai-sagemaker-stack/openwebui --follow --region eu-west-1
```

#### OpenWebUI Loads but No Models Available

**Cause:** OpenWebUI cannot reach the API Gateway endpoint.

**Fix:** The `OPENAI_API_BASE_URL` is set in the ECS Task Definition from the CloudFormation template. Verify the API Gateway URL is correct in the stack outputs:

```bash
aws cloudformation describe-stacks --stack-name openai-sagemaker-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`ApiGatewayEndpoint`].OutputValue' --output text
```

This URL with `/v1` appended should match what OpenWebUI uses.

---

### Useful AWS Console Links (eu-west-1)

| Service | Direct Link |
|---------|------------|
| CloudFormation Stacks | [eu-west-1.console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks](https://eu-west-1.console.aws.amazon.com/cloudformation/home?region=eu-west-1#/stacks) |
| SageMaker Endpoints | [eu-west-1.console.aws.amazon.com/sagemaker/home?region=eu-west-1#/endpoints](https://eu-west-1.console.aws.amazon.com/sagemaker/home?region=eu-west-1#/endpoints) |
| Lambda Functions | [eu-west-1.console.aws.amazon.com/lambda/home?region=eu-west-1#/functions](https://eu-west-1.console.aws.amazon.com/lambda/home?region=eu-west-1#/functions) |
| API Gateway APIs | [eu-west-1.console.aws.amazon.com/apigateway/home?region=eu-west-1#/apis](https://eu-west-1.console.aws.amazon.com/apigateway/home?region=eu-west-1#/apis) |
| ECS Clusters | [eu-west-1.console.aws.amazon.com/ecs/v2/clusters](https://eu-west-1.console.aws.amazon.com/ecs/v2/clusters?region=eu-west-1) |
| Service Quotas (SageMaker) | [eu-west-1.console.aws.amazon.com/servicequotas/home/services/sagemaker/quotas](https://eu-west-1.console.aws.amazon.com/servicequotas/home/services/sagemaker/quotas) |
| CloudWatch Logs | [eu-west-1.console.aws.amazon.com/cloudwatch/home?region=eu-west-1#logsV2:log-groups](https://eu-west-1.console.aws.amazon.com/cloudwatch/home?region=eu-west-1#logsV2:log-groups) |
| VPC Subnets | [eu-west-1.console.aws.amazon.com/vpc/home?region=eu-west-1#subnets:](https://eu-west-1.console.aws.amazon.com/vpc/home?region=eu-west-1#subnets:) |
