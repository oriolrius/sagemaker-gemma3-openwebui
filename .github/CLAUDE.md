# .github/

GitHub Actions CI/CD workflows.

## Workflows

- `deploy.yml` — Deploy full stack. Manual trigger (`workflow_dispatch`). Inputs: `stack_name`, `model_id`, `sagemaker_instance`. 40-min timeout. Packages Lambda, uploads to S3, deploys CFN, tests endpoints.
- `destroy.yml` — Destroy stack. Requires typing "DESTROY" to confirm. Deletes CFN stack + S3 bucket, verifies cleanup.

## Required Secrets

`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_REGION`, `VPC_ID`, `SUBNET_ID`, `SUBNET_ID_2`.
