---
title: Deploy codabench-loadtest on AWS
parent: Deploying on the cloud
nav_order: 1
---

This Terraform project deploys the load-testing infrastructure for Codabench
across three AWS regions. It creates the machines that **generate** the load —
the Codabench target infrastructure (the thing we're testing) is deployed
separately and already exists.

## What gets deployed

### Paris (eu-west-1) — same VPC as Codabench

Lives inside the existing Codabench VPC so it can reach the ALB internally
and monitor RabbitMQ directly.

| Resource | Type | Role |
| ---------- | ------ | ------ |
| Locust master | 1 × t3.medium | Orchestrates workers, serves the web UI on :8089 |
| Locust workers | ASG 2–6 × t3.medium | Generate HTTP load against the ALB |
| Playwright | 1 × t3.large | Measures perceived frontend latency with headless Chromium |

New private subnet: `10.0.21.0/24` — internet access goes through the
existing NAT Gateway.

### US East (us-east-1) — separate VPC

| Resource | Type | Role |
| ---------- | ------ | ------ |
| Locust workers | ASG 2–4 × t3.medium | Headless load from the US |

New VPC `10.1.0.0/16` with a public subnet. Traffic goes over the **public
internet** to the ALB in Paris — no VPC peering, because we want to measure
real user latency from North America.

### Asia Pacific (ap-southeast-1) — separate VPC

| Resource | Type | Role |
| ---------- | ------ | ------ |
| Locust workers | ASG 2–4 × t3.medium | Headless load from Singapore |

Same design as US East, VPC `10.2.0.0/16`. Measures real latency from Asia.

### Shared resources

| Resource | Region | Role |
| ---------- | -------- | ------ |
| NLB `codabench-loadtest-master-nlb` | eu-west-1 | Exposes master :5557-5558 to US/Asia workers (TCP passthrough) |
| S3 bucket `codabench-loadtest-results` | eu-west-1 | Collects CSV results |
| IAM role `codabench-loadtest-role` | global | SSM access + S3 write for results |
| 3 instance profiles | one per region | Attach the IAM role to EC2 in each region |

## Architecture diagram

![Architecture diagram](/docs/images/loadtest_architecture.jpg)

## Prerequisites

- AWS CLI configured with a `codabench` profile
- Terraform >= 1.0
- The Codabench infrastructure must already be deployed (VPC, ALB, app)

## Usage

```bash
# 1. Initialize Terraform (downloads providers, configures S3 backend)
cd cloud/aws/deploy
terraform init

# 2. Preview what will be created
terraform plan

# 3. Deploy
terraform apply

# 5. Connect to any instance via SSM
aws ssm start-session \
  --target <instance-id> \
  --profile codabench
```

## Tear down

```bash
terraform destroy
```

This destroys only the load-generator infrastructure. The Codabench target infrastructure is untouched (separate Terraform state).
