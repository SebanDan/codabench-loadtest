---
title: Setup loadtesting on AWS
parent: Deploying on the cloud
nav_order: 2
---

## AWS Infrastructure

The load-generator infrastructure is managed by Terraform in `cloud/aws/deploy/`. It provisions Locust instances across 3 AWS regions (Paris, US East, Asia Pacific) to simulate geographically distributed users.

Credentials are stored in AWS SSM Parameter Store (no secrets in code):

| Parameter | Type |
| ----------- | ------ |
| `/codabench-loadtest/rabbitmq-user` | String |
| `/codabench-loadtest/rabbitmq-password` | SecureString |
| `/codabench-loadtest/codabench-username` | String |
| `/codabench-loadtest/codabench-password` | SecureString |

Terraform reads these automatically and injects them into `.env` and `.github/env/prod.env` on each instance at boot.

## Usage

### Installation on AWS instances

When deploying with terraform, this repository will be cloned at `/opt/codabench-loadtest` on the ec2 instance.

Connect to the desired instance using an SSM Connection:

```bash
   aws ssm start-session --target "<i-xxxxxxxx>" --profile codabench
```

The `.github/env/prod.env` file is auto-provisioned by user-data at boot. After reviewing it, you can run the following command:

***Note: If `uv` is not on the path, use `/root/.local/bin/uv` instead***

```bash
uv run locust --env prod
```

It is possible to filter on a specific user (for instance here the SmokeUser) by running.

```bash
uv run locust SmokeUser --env prod
```

The results of the tests can be found at `/opt/codabench-loadtest/reports/``

### Running on multiple machine

This tool supports the locust master/worker capabilities. To proceed, follow this steps:

On the master instance, edit the `locust.conf` file and set:

- `master=True`
- `experted-worker=N` (N being the number of workers required).

When ready, run the following command to make it wait for the worker. Don't hesitate to provide more argument if needed.

```bash
cd /opt/codabench-loadtest
uv run locust
```

***Note: You should be seeing: Waiting for workers to be ready, 0 of N connected in the console.***

On the each worker instances, edit the `locust.conf` file and set:

- `worker=True`
- `master-host=X.X.X.X # (ip adress of the locust master instance)`

When ready, run the previous command on each worker instance in order to connect them to the master. Once connected, the scenario will be transmited by the master to the workers.

### Monitoring RabbitMQ

In order to measure RabbitMQ behavior under load, open a new ssm connection on the master instance, and execute the following command:

```bash
   cd /opt/codabench-loadtest
   uv run python -m codabench_loadtest.monitors.rabbitmq_monitor \
     --duration 900 --interval 5 --output runs/rabbit.csv
```

### Running tests using scripts (WIP)

You can configure and launch tests using the SSM-based scripts below.

```bash
# Run a normal test with 50 users for 10 minutes
./scripts/run_test.sh --tags normal --users 50 --duration 10m

# Run the heavy (OOM) scenario, Paris only
./scripts/run_test.sh --tags heavy --users 10 --duration 5m --paris-only

# Run the cancellation scenario on a specific branch
./scripts/run_test.sh --tags clumsy --users 20 --duration 15m --branch feat/new-scenario
```

The `run_test.sh` script:

1. Pulls the latest code on all instances (`git pull` + `uv sync`)
2. Restarts Locust master and Paris workers with the requested tags
3. Starts headless runs on remote regions (US East, Asia Pacific)

Use `--skip-pull` to skip the git pull step if code hasn't changed.

### Stop a running test

```bash
./scripts/stop_test.sh             # Stop all regions
./scripts/stop_test.sh --paris-only  # Stop Paris only
```

## Troubleshouting

### ALB unreachable from Paris (hairpin NAT)

**Symptom:** curling from the Locust master to the ALB DNS returns HTTP 000 / connection timed out.

**Cause:** the ALB is internet-facing (public IPs only). The Locust master is in a private subnet. Traffic goes out through the NAT Gateway to the ALB's public IPs, but the return path doesn't work (hairpin NAT is not supported by AWS NAT Gateway).

**Solution:** Paris tests point directly at `10.0.11.11:80` (Caddy) instead of the ALB DNS. Remote regions (US East, Asia Pacific) continue to use the ALB over the public internet. Be sure to update the `prod.env` variables to target either the ALB from or Private IP adress depending on the region.

### Problem 3: Missing security groups

**Symptom:** connection timeout to `10.0.11.11` on ports 80 or 15672.

**Cause:** the security group rules did not allow Locust traffic to reach the Codabench instance's security group.

**Solution:** added 3 rules in `security_group.tf` of the Paris module:

- Egress: Locust → Codabench SG, port 80 (test traffic)
- Ingress: Codabench SG ← Locust SG, port 80 (accept the traffic)
- Ingress: ALB SG ← Locust SG, port 80 (for future ALB tests)

(The RabbitMQ `:15672` rule already existed.)
