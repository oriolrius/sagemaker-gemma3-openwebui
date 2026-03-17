# SageMaker Endpoint Quotas - eu-west-1 (Ireland)

**Account:** 658203403846 (DevOps sandbox)
**Region:** eu-west-1 (Ireland)
**Last Updated:** 2026-03-17
**Total Instances Across Active Endpoints:** 20

> **Note:** Pricing shown is approximate SageMaker Real-Time Inference on-demand pricing for eu-west-1.
> Quotas are per-account and per-region. Always verify current values in the [Service Quotas console](https://eu-west-1.console.aws.amazon.com/servicequotas/home/services/sagemaker/quotas).
> Actual prices may vary. Check [AWS SageMaker Pricing](https://aws.amazon.com/sagemaker/pricing/) for current rates.

---

## GPU Instances (Required for TGI)

These instances support **HuggingFace TGI** inference. Gemma 3 and other modern models require **bfloat16** precision, which is only available on **Ampere+ GPUs** (g5, g6 series). T4 GPUs (g4dn) only support fp16 and are limited to models that do not require bfloat16.

| Instance Type | Quota | Price/Hour | vCPUs | RAM | GPU | GPU Model | GPU Memory | GPU Arch | Notes |
|---------------|-------|------------|-------|-----|-----|-----------|------------|----------|-------|
| **ml.g4dn.xlarge** | 1 | ~$0.74 | 4 | 16 GB | 1 | NVIDIA T4 Tensor Core | 16 GB GDDR6 | Turing (SM75) | fp16 only -- NOT for Gemma 3 |
| **ml.g4dn.2xlarge** | 1 | ~$1.05 | 8 | 32 GB | 1 | NVIDIA T4 Tensor Core | 16 GB GDDR6 | Turing (SM75) | fp16 only -- NOT for Gemma 3 |

### NVIDIA A10G GPU Specifications (Recommended for Gemma 3)

| Specification | Value |
|---------------|-------|
| Architecture | Ampere (GA102) |
| CUDA Cores | 9,216 |
| Tensor Cores | 288 (3rd gen) |
| GPU Memory | 24 GB GDDR6 |
| Memory Bandwidth | 600 GB/s |
| FP32 Performance | 31.2 TFLOPS |
| FP16/BF16 Performance | 125 TFLOPS (with Tensor Cores) |
| TF32 Performance | 62.5 TFLOPS |
| TDP | 150W |
| Compute Capability | 8.6 |

### NVIDIA T4 GPU Specifications (Legacy -- fp16 only)

| Specification | Value |
|---------------|-------|
| Architecture | Turing (TU104) |
| CUDA Cores | 2,560 |
| Tensor Cores | 320 |
| GPU Memory | 16 GB GDDR6 |
| Memory Bandwidth | 320 GB/s |
| FP32 Performance | 8.1 TFLOPS |
| FP16 Performance | 65 TFLOPS (with Tensor Cores) |
| INT8 Performance | 130 TOPS (with Tensor Cores) |
| TDP | 70W |
| Compute Capability | 7.5 |

### GPU Instances with Zero Quota (Request Increase if Needed)

| Instance Type | Quota | Price/Hour | vCPUs | RAM | GPU | GPU Model | GPU Memory |
|---------------|-------|------------|-------|-----|-----|-----------|------------|
| ml.g4dn.4xlarge | 0 | ~$1.60 | 16 | 64 GB | 1 | NVIDIA T4 | 16 GB |
| ml.g4dn.8xlarge | 0 | ~$2.90 | 32 | 128 GB | 1 | NVIDIA T4 | 16 GB |
| ml.g4dn.12xlarge | 0 | ~$5.20 | 48 | 192 GB | 4 | NVIDIA T4 | 64 GB (4x16) |
| ml.g4dn.16xlarge | 0 | ~$5.80 | 64 | 256 GB | 1 | NVIDIA T4 | 16 GB |
| **ml.g5.xlarge** | 0 | ~$1.41 | 4 | 16 GB | 1 | NVIDIA A10G | 24 GB | **Recommended** - bfloat16 support for Gemma 3 |
| **ml.g5.2xlarge** | 0 | ~$1.58 | 8 | 32 GB | 1 | NVIDIA A10G | 24 GB | More CPU/RAM for larger models |
| ml.g5.4xlarge | 0 | ~$2.12 | 16 | 64 GB | 1 | NVIDIA A10G | 24 GB |
| ml.g5.8xlarge | 0 | ~$3.18 | 32 | 128 GB | 1 | NVIDIA A10G | 24 GB |
| ml.g5.12xlarge | 0 | ~$7.09 | 48 | 192 GB | 4 | NVIDIA A10G | 96 GB (4x24) |
| ml.g5.16xlarge | 0 | ~$5.36 | 64 | 256 GB | 1 | NVIDIA A10G | 24 GB |
| ml.g5.24xlarge | 0 | ~$10.63 | 96 | 384 GB | 4 | NVIDIA A10G | 96 GB (4x24) |
| ml.g5.48xlarge | 0 | ~$21.26 | 192 | 768 GB | 8 | NVIDIA A10G | 192 GB (8x24) |
| ml.g6.xlarge | 0 | ~$0.98 | 4 | 16 GB | 1 | NVIDIA L4 | 24 GB |
| ml.g6.2xlarge | 0 | ~$1.23 | 8 | 32 GB | 1 | NVIDIA L4 | 24 GB |
| ml.g6e.xlarge | 0 | ~$1.86 | 4 | 32 GB | 1 | NVIDIA L40S | 48 GB |
| ml.g6e.2xlarge | 0 | ~$2.30 | 8 | 64 GB | 1 | NVIDIA L40S | 48 GB |

---

## CPU Instances - General Purpose (M-Series)

Best for balanced workloads with moderate compute and memory requirements.

| Instance Type | Quota | Price/Hour | vCPUs | RAM | Storage | Network | Notes |
|---------------|-------|------------|-------|-----|---------|---------|-------|
| ml.m5.large | 4 | ~$0.12 | 2 | 8 GB | EBS | Up to 10 Gbps | |
| ml.m5.xlarge | 2 | ~$0.23 | 4 | 16 GB | EBS | Up to 10 Gbps | |
| ml.m5.2xlarge | 1 | ~$0.46 | 8 | 32 GB | EBS | Up to 10 Gbps | |
| ml.m5d.large | 4 | ~$0.14 | 2 | 8 GB | 1x75 NVMe SSD | Up to 10 Gbps | Local NVMe |
| ml.m5d.xlarge | 2 | ~$0.27 | 4 | 16 GB | 1x150 NVMe SSD | Up to 10 Gbps | Local NVMe |
| ml.m5d.2xlarge | 1 | ~$0.54 | 8 | 32 GB | 1x300 NVMe SSD | Up to 10 Gbps | Local NVMe |
| ml.m6g.large | 4 | ~$0.10 | 2 | 8 GB | EBS | Up to 10 Gbps | Graviton2 (ARM) |
| ml.m6g.xlarge | 2 | ~$0.20 | 4 | 16 GB | EBS | Up to 10 Gbps | Graviton2 (ARM) |
| ml.m6g.2xlarge | 1 | ~$0.39 | 8 | 32 GB | EBS | Up to 10 Gbps | Graviton2 (ARM) |
| ml.m6gd.large | 4 | ~$0.11 | 2 | 8 GB | 1x118 NVMe SSD | Up to 10 Gbps | Graviton2 + NVMe |
| ml.m6gd.xlarge | 2 | ~$0.23 | 4 | 16 GB | 1x237 NVMe SSD | Up to 10 Gbps | Graviton2 + NVMe |
| ml.m6gd.2xlarge | 1 | ~$0.45 | 8 | 32 GB | 1x474 NVMe SSD | Up to 10 Gbps | Graviton2 + NVMe |

---

## CPU Instances - Compute Optimized (C-Series)

Best for compute-intensive workloads requiring high CPU performance.

| Instance Type | Quota | Price/Hour | vCPUs | RAM | Storage | Network | Notes |
|---------------|-------|------------|-------|-----|---------|---------|-------|
| ml.c5.large | 4 | ~$0.10 | 2 | 4 GB | EBS | Up to 10 Gbps | |
| ml.c5.xlarge | 2 | ~$0.20 | 4 | 8 GB | EBS | Up to 10 Gbps | |
| ml.c5.2xlarge | 1 | ~$0.40 | 8 | 16 GB | EBS | Up to 10 Gbps | |
| ml.c5.4xlarge | 1 | ~$0.80 | 16 | 32 GB | EBS | Up to 10 Gbps | |
| ml.c5d.large | 4 | ~$0.11 | 2 | 4 GB | 1x50 NVMe SSD | Up to 10 Gbps | Local NVMe |
| ml.c5d.xlarge | 2 | ~$0.23 | 4 | 8 GB | 1x100 NVMe SSD | Up to 10 Gbps | Local NVMe |
| ml.c5d.2xlarge | 1 | ~$0.46 | 8 | 16 GB | 1x200 NVMe SSD | Up to 10 Gbps | Local NVMe |
| ml.c6g.large | 4 | ~$0.09 | 2 | 4 GB | EBS | Up to 10 Gbps | Graviton2 (ARM) |
| ml.c6g.xlarge | 2 | ~$0.17 | 4 | 8 GB | EBS | Up to 10 Gbps | Graviton2 (ARM) |
| ml.c6g.2xlarge | 1 | ~$0.34 | 8 | 16 GB | EBS | Up to 10 Gbps | Graviton2 (ARM) |
| ml.c6g.4xlarge | 1 | ~$0.68 | 16 | 32 GB | EBS | Up to 10 Gbps | Graviton2 (ARM) |
| ml.c6gd.large | 4 | ~$0.10 | 2 | 4 GB | 1x118 NVMe SSD | Up to 10 Gbps | Graviton2 + NVMe |
| ml.c6gd.xlarge | 2 | ~$0.19 | 4 | 8 GB | 1x237 NVMe SSD | Up to 10 Gbps | Graviton2 + NVMe |
| ml.c6gd.2xlarge | 1 | ~$0.39 | 8 | 16 GB | 1x474 NVMe SSD | Up to 10 Gbps | Graviton2 + NVMe |
| ml.c6gn.large | 4 | ~$0.11 | 2 | 4 GB | EBS | Up to 25 Gbps | Graviton2 + Enhanced Network |
| ml.c6gn.xlarge | 2 | ~$0.22 | 4 | 8 GB | EBS | Up to 25 Gbps | Graviton2 + Enhanced Network |
| ml.c6gn.2xlarge | 1 | ~$0.43 | 8 | 16 GB | EBS | Up to 25 Gbps | Graviton2 + Enhanced Network |
| ml.c7g.large | 4 | ~$0.09 | 2 | 4 GB | EBS | Up to 12.5 Gbps | Graviton3 (ARM) |
| ml.c7g.xlarge | 2 | ~$0.18 | 4 | 8 GB | EBS | Up to 12.5 Gbps | Graviton3 (ARM) |
| ml.c7g.2xlarge | 1 | ~$0.36 | 8 | 16 GB | EBS | Up to 15 Gbps | Graviton3 (ARM) |
| ml.c7g.4xlarge | 1 | ~$0.73 | 16 | 32 GB | EBS | Up to 15 Gbps | Graviton3 (ARM) |

---

## CPU Instances - Memory Optimized (R-Series)

Best for memory-intensive workloads, large datasets, or models requiring significant RAM.

| Instance Type | Quota | Price/Hour | vCPUs | RAM | Storage | Network | Notes |
|---------------|-------|------------|-------|-----|---------|---------|-------|
| ml.r5.large | 1 | ~$0.15 | 2 | 16 GB | EBS | Up to 10 Gbps | |
| ml.r5.xlarge | 1 | ~$0.30 | 4 | 32 GB | EBS | Up to 10 Gbps | |
| ml.r5d.large | 1 | ~$0.17 | 2 | 16 GB | 1x75 NVMe SSD | Up to 10 Gbps | Local NVMe |
| ml.r5d.xlarge | 1 | ~$0.35 | 4 | 32 GB | 1x150 NVMe SSD | Up to 10 Gbps | Local NVMe |
| ml.r6g.large | 1 | ~$0.13 | 2 | 16 GB | EBS | Up to 10 Gbps | Graviton2 (ARM) |
| ml.r6g.xlarge | 1 | ~$0.25 | 4 | 32 GB | EBS | Up to 10 Gbps | Graviton2 (ARM) |
| ml.r6gd.large | 1 | ~$0.14 | 2 | 16 GB | 1x118 NVMe SSD | Up to 10 Gbps | Graviton2 + NVMe |
| ml.r6gd.xlarge | 1 | ~$0.29 | 4 | 32 GB | 1x237 NVMe SSD | Up to 10 Gbps | Graviton2 + NVMe |

---

## Burstable Instances (T-Series)

Best for development, testing, and low-traffic workloads. Uses CPU credits for bursting.

| Instance Type | Quota | Price/Hour | vCPUs | RAM | Baseline CPU | Network | Notes |
|---------------|-------|------------|-------|-----|--------------|---------|-------|
| ml.t2.medium | 6 | ~$0.06 | 2 | 4 GB | 20% | Low to Moderate | Burstable, cost-effective |
| ml.t2.large | 6 | ~$0.11 | 2 | 8 GB | 30% | Low to Moderate | Burstable |
| ml.t2.xlarge | 6 | ~$0.22 | 4 | 16 GB | 40% | Moderate | Burstable |
| ml.t2.2xlarge | 6 | ~$0.45 | 8 | 32 GB | 40% | Moderate | Burstable |

---

## Cost Comparison Summary

### GPU Instances (Available)

| Instance | Hourly | Daily (24h) | Monthly (720h) | Best For |
|----------|--------|-------------|----------------|----------|
| **ml.g5.xlarge** | ~$1.41 | ~$33.84 | ~$1,015 | **Recommended** - Gemma 3, bfloat16 models |
| ml.g5.2xlarge | ~$1.58 | ~$37.92 | ~$1,138 | Larger models, more CPU/RAM |
| ml.g4dn.xlarge | ~$0.74 | ~$17.76 | ~$533 | fp16-only models (NOT Gemma 3) |
| ml.g4dn.2xlarge | ~$1.05 | ~$25.20 | ~$756 | fp16-only, more CPU/RAM |

### CPU Instances (Cheapest Available)

| Instance | Hourly | Daily (24h) | Monthly (720h) | Best For |
|----------|--------|-------------|----------------|----------|
| ml.t2.medium | ~$0.06 | ~$1.44 | ~$43 | Dev/test, minimal inference |
| ml.c6g.large | ~$0.09 | ~$2.16 | ~$65 | Lightweight CPU inference |
| ml.m6g.large | ~$0.10 | ~$2.40 | ~$72 | Balanced workloads |

---

## Important Notes

### TGI Compatibility

- **GPU Required**: HuggingFace TGI container requires NVIDIA GPU instances (g4dn, g5, g6 series)
- **bfloat16 Required for Gemma 3**: Gemma 3 models require bfloat16 precision, which is only available on Ampere+ GPUs (g5: A10G, g6: L4, g6e: L40S). T4 GPUs (g4dn) only support fp16
- **ARM Not Supported**: Graviton-based instances (m6g, c6g, c7g, r6g) are NOT compatible with the TGI GPU container
- **Minimum GPU Memory**: Most LLMs require at least 8GB GPU memory; A10G's 24GB is sufficient for models up to ~7B parameters in bfloat16

### Requesting Quota Increases

#### Via AWS Console

1. Open [Service Quotas for SageMaker in eu-west-1](https://eu-west-1.console.aws.amazon.com/servicequotas/home/services/sagemaker/quotas)
2. Search for the instance type (e.g., `ml.g4dn.xlarge`)
3. Click the quota name (e.g., **"ml.g4dn.xlarge for endpoint usage"**)
4. Click **"Request increase at account level"** (orange button, top-right)
5. Enter the desired quota value (e.g., `1`)
6. Click **"Request"**

#### Via AWS CLI

```bash
# Find the quota code
QUOTA_CODE=$(aws service-quotas list-service-quotas \
  --service-code sagemaker --region eu-west-1 \
  --query "Quotas[?contains(QuotaName, 'g4dn.xlarge') && contains(QuotaName, 'endpoint')].QuotaCode" \
  --output text)

# Request increase
aws service-quotas request-service-quota-increase \
  --service-code sagemaker --quota-code "$QUOTA_CODE" \
  --desired-value 1 --region eu-west-1

# Check status
aws service-quotas list-requested-service-quota-change-history \
  --service-code sagemaker --region eu-west-1 \
  --query "RequestedQuotas[?contains(QuotaName, 'g4dn')].[QuotaName,Status,DesiredValue]" \
  --output table
```

#### Approval Times

- Sandbox/lab accounts: often automatic (minutes to hours)
- New production accounts: 1-3 business days
- Large increases: may require support case with justification

### Cost Optimization Tips

- **Spot Instances**: Not available for SageMaker Real-Time Inference
- **Savings Plans**: Up to 64% discount with 1-year or 3-year commitment
- **Auto-scaling**: Configure endpoint auto-scaling to scale to 0 during idle periods
- **Delete When Unused**: SageMaker endpoints charge continuously while running

---

## References

- [AWS SageMaker Pricing](https://aws.amazon.com/sagemaker/pricing/)
- [AWS Service Quotas Console](https://console.aws.amazon.com/servicequotas/)
- [SageMaker Instance Types](https://aws.amazon.com/sagemaker/pricing/)
- [NVIDIA T4 Specifications](https://www.nvidia.com/en-us/data-center/tesla-t4/)
- [Vantage Instance Pricing](https://instances.vantage.sh/)
