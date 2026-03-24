# .github/

GitHub Actions CI/CD workflows.

## Workflows

- `deploy.yml` — Deploy full stack. Manual trigger. Inputs: `stack_name`, `model_id`, `sagemaker_instance`, `ec2_instance`. 40-min timeout.
- `destroy.yml` — Destroy stack. Requires typing "DESTROY". Deletes CFN stack + S3 bucket.

## Required Secrets

`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`, `AWS_REGION`, `VPC_ID`, `SUBNET_ID`.
