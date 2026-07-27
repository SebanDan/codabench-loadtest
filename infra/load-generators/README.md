# Locust Load Generators — Infrastructure

This Terraform project deploys the load-testing infrastructure for Codabench
across three AWS regions. It creates the machines that **generate** the load —
the Codabench target infrastructure (the thing we're testing) is deployed
separately and already exists.

## What gets deployed

### Paris (eu-west-1) — same VPC as Codabench

Lives inside the existing Codabench VPC so it can reach the ALB internally
and monitor RabbitMQ directly.

| Resource | Type | Role |
|----------|------|------|
| Locust master | 1 × t3.medium | Orchestrates workers, serves the web UI on :8089 |
| Locust workers | ASG 2–6 × t3.medium | Generate HTTP load against the ALB |
| Playwright | 1 × t3.large | Measures perceived frontend latency with headless Chromium |

New private subnet: `10.0.21.0/24` — internet access goes through the
existing NAT Gateway.

### US East (us-east-1) — separate VPC

| Resource | Type | Role |
|----------|------|------|
| Locust workers | ASG 2–4 × t3.medium | Headless load from the US |

New VPC `10.1.0.0/16` with a public subnet. Traffic goes over the **public
internet** to the ALB in Paris — no VPC peering, because we want to measure
real user latency from North America.

### Asia Pacific (ap-southeast-1) — separate VPC

| Resource | Type | Role |
|----------|------|------|
| Locust workers | ASG 2–4 × t3.medium | Headless load from Singapore |

Same design as US East, VPC `10.2.0.0/16`. Measures real latency from Asia.

### Shared resources

| Resource | Region | Role |
|----------|--------|------|
| S3 bucket `codabench-loadtest-results` | eu-west-1 | Collects CSV results from all regions |
| IAM role `codabench-loadtest-role` | global | SSM access + S3 write for results |
| 3 instance profiles | one per region | Attach the IAM role to EC2 in each region |

## Architecture diagram

```
                         Operator laptop
                             │
                             │ SSM port forward :8089
                             ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AWS Account 857753985711                                │
│                                                                              │
│  ┌── eu-west-1 (Paris) ────────────────────────────────────────────────────┐ │
│  │                                                                         │ │
│  │  VPC: codabench-prodlike-vpc  10.0.0.0/16                               │ │
│  │                                                                         │ │
│  │  ┌─ Public subnets (existing) ────────────────────────────────────────┐ │ │
│  │  │  10.0.1.0/24              10.0.2.0/24                              │ │ │
│  │  │                                                                    │ │ │
│  │  │  ┌──────────────────┐     ┌────────────┐                           │ │ │
│  │  │  │ ALB              │     │ NAT Gateway│                           │ │ │
│  │  │  │ :80 (existing)   │     │ (existing) │                           │ │ │
│  │  │  └────────▲─────────┘     └──────┬─────┘                           │ │ │
│  │  └───────────┼──────────────────────┼─────────────────────────────────┘ │ │
│  │              │                      │                                   │ │
│  │              │ ① :80                │ ③ :443                            │ │
│  │              │ test traffic         │ pip/git                           │ │
│  │  ┌─ Locust subnet (NEW) ───────────┼──────────────────────────────────┐ │ │
│  │  │  10.0.21.0/24                   │                                  │ │ │
│  │  │                                 │                                  │ │ │
│  │  │  ┌───────────────────┐          │       ┌───────────────────┐      │ │ │
│  │  │  │ Locust Master     │──────────┘       │ Playwright        │      │ │ │
│  │  │  │ t3.medium         │                  │ t3.large          │      │ │ │
│  │  │  │ :8089 web UI      │                  │ Chromium headless │      │ │ │
│  │  │  │ :5557-5558        │                  └───────────────────┘      │ │ │
│  │  │  └─────────┬─────┬──┘                                             │ │ │
│  │  │    :5557   │     │ ② :15672                                       │ │ │
│  │  │  ┌─────────▼──┐  │ monitoring                                     │ │ │
│  │  │  │ Workers    │  │                                                │ │ │
│  │  │  │ ASG 2-6    │  │   SG: codabench-loadtest-locust-sg             │ │ │
│  │  │  │ t3.medium  │  │                                                │ │ │
│  │  │  └────────────┘  │                                                │ │ │
│  │  └──────────────────┼────────────────────────────────────────────────┘ │ │
│  │                     │                                                  │ │
│  │  ┌─ Codabench subnets (existing) ────────────────────────────────────┐ │ │
│  │  │  10.0.11.0/24              10.0.12.0/24                           │ │ │
│  │  │                                                                   │ │ │
│  │  │  ┌───────────────────┐                                            │ │ │
│  │  │  │ Codabench App     │◄───────────┘                               │ │ │
│  │  │  │ 10.0.11.11        │  queue_metrics_watcher.py                  │ │ │
│  │  │  │ :8000  Django     │                                            │ │ │
│  │  │  │ :5672  RabbitMQ   │     ┌──────────────┐   ┌──────────────┐    │ │ │
│  │  │  │ :15672 Mgmt API   │     │ Workers ASG  │   │ MinIO x4     │    │ │ │
│  │  │  └───────────────────┘     │ (existing)   │   │ (existing)   │    │ │ │
│  │  │                            └──────────────┘   └──────────────┘    │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  │                                                                        │ │
│  │  ┌─ S3 ──────────────────────────────────────────────────────────────┐ │ │
│  │  │  codabench-loadtest-results (NEW)                                 │ │ │
│  │  │  ├── paris/           CSV Locust + queue metrics                  │ │ │
│  │  │  ├── us-east/         CSV Locust                                  │ │ │
│  │  │  └── ap-southeast/    CSV Locust                                  │ │ │
│  │  └───────────────────────────────────────────────────────────────────┘ │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌── us-east-1 (Virginia) ─────────────────────────────────────────────────┐ │
│  │                                                                         │ │
│  │  VPC: codabench-loadtest-us-east-vpc  10.1.0.0/16 (NEW)                 │ │
│  │                                                                         │ │
│  │  ┌─ Public subnet ─────────────────────────────────────────────────┐    │ │
│  │  │  10.1.1.0/24                                                    │    │ │
│  │  │                                                                 │    │ │
│  │  │  ┌────────────────┐                                             │    │ │
│  │  │  │ Workers ASG    │── :80 ──► INTERNET ──► ALB Paris            │    │ │
│  │  │  │ 2-4 t3.medium  │── :443 ─► pip, git, S3                     │    │ │
│  │  │  │ headless       │                                             │    │ │
│  │  │  │ manual via SSM │  No VPC peering = real US user latency      │    │ │
│  │  │  └────────────────┘                                             │    │ │
│  │  └─────────────────────────────────────────────────────────────────┘    │ │
│  │  IGW (NEW)                                                              │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌── ap-southeast-1 (Singapore) ───────────────────────────────────────────┐ │
│  │                                                                         │ │
│  │  VPC: codabench-loadtest-ap-southeast-vpc  10.2.0.0/16 (NEW)            │ │
│  │                                                                         │ │
│  │  ┌─ Public subnet ─────────────────────────────────────────────────┐    │ │
│  │  │  10.2.1.0/24                                                    │    │ │
│  │  │                                                                 │    │ │
│  │  │  ┌────────────────┐                                             │    │ │
│  │  │  │ Workers ASG    │── :80 ──► INTERNET ──► ALB Paris            │    │ │
│  │  │  │ 2-4 t3.medium  │── :443 ─► pip, git, S3                     │    │ │
│  │  │  │ headless       │                                             │    │ │
│  │  │  │ manual via SSM │  No VPC peering = real Asia user latency    │    │ │
│  │  │  └────────────────┘                                             │    │ │
│  │  └─────────────────────────────────────────────────────────────────┘    │ │
│  │  IGW (NEW)                                                              │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
│                                                                              │
│  ┌── IAM (global) ─────────────────────────────────────────────────────────┐ │
│  │  Role: codabench-loadtest-role                                          │ │
│  │    ├── AmazonSSMManagedInstanceCore                                     │ │
│  │    └── s3:PutObject/GetObject -> codabench-loadtest-results             │ │
│  │  Instance profiles: paris / us-east / ap-southeast                      │ │
│  └─────────────────────────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────────────────────────┘

Network flows:

  ①  Test traffic (HTTP :80)
     Paris: Locust -> 10.0.11.11:80 Caddy (direct, private)
            The ALB is internet-facing (public IPs only), so Paris
            instances cannot reach it (hairpin NAT not supported).
     US/Asia: Locust -> internet -> ALB (real user latency)

  ②  RabbitMQ monitoring (HTTP :15672)
     Locust master -> 10.0.11.11 (direct, private)
     Used by queue_metrics_watcher.py only, not by Locust workers

  ③  Internet access (HTTPS :443)
     Paris: via existing NAT Gateway
     US/Asia: via dedicated IGW (public subnet)
     For: pip install, git clone, S3 result upload
```

## Prerequisites

- AWS CLI configured with a `codabench` profile
- Terraform >= 1.0
- The Codabench infrastructure must already be deployed (VPC, ALB, app)

## Usage

```bash
# 1. Initialize Terraform (downloads providers, configures S3 backend)
cd infra/load-generators
terraform init

# 2. Preview what will be created
terraform plan

# 3. Deploy
terraform apply

# 4. Connect to the Locust master web UI
aws ssm start-session \
  --target "$(terraform output -raw paris_locust_master_id)" \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["8089"],"localPortNumber":["8089"]}' \
  --profile codabench
# Then open http://localhost:8089

# 5. Connect to any instance via SSM
aws ssm start-session \
  --target <instance-id> \
  --profile codabench
```

## Running tests

Locust starts automatically on boot (master + Paris workers). You can
configure and launch tests from the web UI, or use the SSM-based scripts
below to manage tests from your laptop without recreating instances.

### Via the web UI (simplest)

Locust master auto-starts on boot, so the web UI is available immediately
after `terraform apply`. No script needed — just port-forward and open
your browser:

```bash
aws ssm start-session \
  --target "$(terraform output -raw paris_locust_master_id)" \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["8089"],"localPortNumber":["8089"]}' \
  --profile codabench
```

Then open http://localhost:8089 and configure your test (users, spawn rate, host).

> **Limitation:** the web UI does not support tag filtering. When launched
> from the UI, **all scenarios run together** (smoke + normal + clumsy + heavy).
> To run a specific scenario (e.g. only `heavy`), use `run_test.sh` below —
> it restarts Locust with `--tags` so only the selected scenarios execute.

### Via scripts (tag filtering, multi-region, git pull)

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

### Manual workflow (via SSM + web UI)

```bash
# 1. Port-forward the Locust master UI
aws ssm start-session \
  --target "$(terraform output -raw paris_locust_master_id)" \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["8089"],"localPortNumber":["8089"]}' \
  --profile codabench
# Then open http://localhost:8089 and configure the test from the UI

# 2. (Optional) Start RabbitMQ monitoring from the master
aws ssm start-session --target "$(terraform output -raw paris_locust_master_id)" --profile codabench
# Inside the session:
cd /opt/codabench-loadtest
uv run python queue_metrics_watcher.py --queue submissions --duration 1800
```

### RabbitMQ monitoring

Run the queue metrics collector on the Locust master **in parallel** with
your Locust test. It polls the RabbitMQ Management API and writes CSV with
queue depth, consumer count, publish/deliver rates, and node memory.

```bash
# From an SSM session on the master:
cd /opt/codabench-loadtest
uv run python -m codabench_loadtest.common.rabbitmq_monitor \
  --queue submissions --duration 900 --interval 5 \
  --output runs/<run-name>_rabbit.csv

# Or monitor all queues (omit --queue):
uv run python -m codabench_loadtest.common.rabbitmq_monitor \
  --duration 900 --output runs/<run-name>_rabbit.csv
```

Requires `CODABENCH_RABBITMQ_URL`, `CODABENCH_RABBITMQ_USER`, and
`CODABENCH_RABBITMQ_PASSWORD` in the `.env` file.

### Collect results

```bash
# Download CSV results from all regions
./scripts/collect_results.sh <run-name>

# Generate report
uv run python reports/generate_report.py \
  --regions paris,us-east,ap-southeast \
  --run <run-name>
```

## Tear down

```bash
terraform destroy
```

This destroys only the load-generator infrastructure. The Codabench target
infrastructure is untouched (separate Terraform state).

## File structure

```
load-generators/
├── provider.tf          # 3 AWS providers (paris, us-east, ap-southeast) + S3 backend
├── variables.tf         # All configurable inputs
├── main.tf              # Calls the 3 regional modules
├── outputs.tf           # Instance IDs, ASG names, ALB DNS, S3 bucket
├── s3.tf                # Results collection bucket
├── iam.tf               # IAM role (SSM + S3) + 3 instance profiles
│
├── modules/
│   ├── paris/           # Locust master + workers + Playwright
│   │   ├── data.tf      # Lookups: existing VPC, ALB, security groups
│   │   ├── network.tf   # New subnet 10.0.21.0/24
│   │   ├── security_group.tf  # Locust SG + RabbitMQ ingress on Codabench SG
│   │   ├── master.tf    # Locust master EC2
│   │   ├── workers.tf   # Locust workers ASG (2-6)
│   │   ├── playwright.tf
│   │   ├── variables.tf
│   │   └── outputs.tf
│   │
│   └── remote_region/   # Reused for US East and Asia Pacific
│       ├── vpc.tf       # Dedicated VPC + public subnet + IGW
│       ├── security_group.tf  # Egress-only (80 + 443)
│       ├── workers.tf   # Headless workers ASG
│       ├── variables.tf
│       └── outputs.tf
│
└── templates/           # EC2 user-data boot scripts (install + auto-start Locust)
    ├── locust_master.sh.tftpl
    ├── locust_worker_paris.sh.tftpl
    ├── locust_worker_remote.sh.tftpl
    └── playwright.sh.tftpl

scripts/                 # Operator scripts (run from your laptop)
├── run_test.sh          # Launch a test via SSM (git pull + restart Locust with params)
├── stop_test.sh         # Stop all running Locust processes via SSM
└── collect_results.sh   # Download CSV results from all regions via S3
```

