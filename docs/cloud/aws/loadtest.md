---
title: Setup loadtesting on AWS
parent: Deploying on the cloud
nav_order: 2
---

## AWS Infrastructure

The load-generator infrastructure is managed by Terraform in `cloud/aws/deploy/`. It provisions Locust instances across 3 AWS regions (Paris, US East, Asia Pacific) to simulate geographically distributed users.

Credentials are stored in AWS SSM Parameter Store (no secrets in code):

| Parameter | Type |
|-----------|------|
| `/codabench-loadtest/rabbitmq-user` | String |
| `/codabench-loadtest/rabbitmq-password` | SecureString |
| `/codabench-loadtest/codabench-username` | String |
| `/codabench-loadtest/codabench-password` | SecureString |

Terraform reads these automatically and injects them into `.env` and `.github/env/prod.env` on each instance at boot. See `docs/test_steps.txt` for detailed test procedures.

## Usage

### Installation on AWS instances

The `prod.env` file is auto-provisioned by user-data at boot. Just run:

```bash
uv run locust --env prod
```

Or use the orchestration scripts:

```bash
./cloud/aws/scripts/run_test.sh --tags normal --users 50 --duration 10m
./cloud/aws/scripts/stop_test.sh
./cloud/aws/scripts/collect_results.sh <run-name>
```

*Note: As the locust test will generate assets on the platform it is required to provide a valid admin username and password in the env file.*

It is possible to filter on a specific user (for instance here the SmokeUser) by running.

```bash
uv run locust SmokeUser
```