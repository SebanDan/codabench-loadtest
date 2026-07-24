# Codabench Infrastructure

## Overview

This Terraform project deploys a production-like Codabench environment on AWS
(`eu-west-1`). All application instances run in **private subnets** with no
public IP. External access goes through an internet-facing ALB; admin access
uses AWS SSM Session Manager (no SSH bastion needed).

```
                    ┌─────────────────────────────────────────────┐
                    │  VPC: codabench-prodlike-vpc  10.0.0.0/16   │
                    │                                             │
                    │  ┌─ Public subnets ───────────────────────┐ │
                    │  │  10.0.1.0/24  (eu-west-1a)             │ │
                    │  │  10.0.2.0/24  (eu-west-1b)             │ │
                    │  │                                        │ │
                    │  │  ┌────────────┐  ┌──────────────────┐  │ │
                    │  │  │ ALB        │  │ ALB MinIO API    │  │ │
                    │  │  │ :80 → app  │  │ :80 → MinIO:9000│  │ │
                    │  │  └─────┬──────┘  └─────────────────┘   │ │
                    │  │        │                                │ │
                    │  │  ┌─────┴──────┐                        │ │
                    │  │  │ NAT Gateway│                        │ │
                    │  │  └────────────┘                        │ │
                    │  └────────────────────────────────────────┘ │
                    │                                             │
                    │  ┌─ Private subnets ──────────────────────┐ │
                    │  │  10.0.11.0/24  (eu-west-1a)            │ │
                    │  │  10.0.12.0/24  (eu-west-1b)            │ │
                    │  │                                        │ │
                    │  │  ┌──────────────┐                      │ │
                    │  │  │ Codabench    │  m6i.4xlarge          │ │
                    │  │  │ 10.0.11.11   │  app :8000            │ │
                    │  │  │              │  RabbitMQ :5672        │ │
                    │  │  └──────┬───────┘                      │ │
                    │  │         │                               │ │
                    │  │  ┌──────┴───────┐  ┌──────────────┐    │ │
                    │  │  │ Workers ASG  │  │ NGINX MinIO  │    │ │
                    │  │  │ 8–15 inst.   │  │ 10.0.11.12   │    │ │
                    │  │  │ c6i.large    │  │ LB :9000/:9001│   │ │
                    │  │  └──────────────┘  └──────┬───────┘    │ │
                    │  │                           │            │ │
                    │  │                    ┌───────┴────────┐   │ │
                    │  │                    │ MinIO ×4       │   │ │
                    │  │                    │ 10.0.11.20–.23 │   │ │
                    │  │                    │ t3.small        │  │ │
                    │  │                    │ 2×100 GB EBS    │  │ │
                    │  │                    └────────────────┘   │ │
                    │  └────────────────────────────────────────┘ │
                    └─────────────────────────────────────────────┘
```

## Components

### VPC & Networking

| Resource | Name | Details |
|----------|------|---------|
| VPC | `codabench-prodlike-vpc` | `10.0.0.0/16` |
| Public subnet 1 | `codabench-prodlike-public-1` | `10.0.1.0/24` — `eu-west-1a` |
| Public subnet 2 | `codabench-prodlike-public-2` | `10.0.2.0/24` — `eu-west-1b` |
| Private subnet 1 | `codabench-prodlike-private-1` | `10.0.11.0/24` — `eu-west-1a` |
| Private subnet 2 | `codabench-prodlike-private-2` | `10.0.12.0/24` — `eu-west-1b` |
| NAT Gateway | `codabench-prodlike-nat-gw` | In public subnet 1; gives private instances internet access |
| Internet Gateway | `codabench-prodlike-igw` | Attached to VPC for public subnets |

### ALB (Application Load Balancers)

Both ALBs are **internet-facing** (`internal = false`), placed in the two public subnets.

| ALB | Listener | Target |
|-----|----------|--------|
| `codabench-prodlike-alb` | `:80` HTTP | Codabench app (port 8000) |
| | `:80` path `/minio-console/*` | MinIO Console via NGINX (port 9001) |
| `codabench-prodlike-minio-api-alb` | `:80` HTTP | MinIO API via NGINX (port 9000) |

### EC2 Instances (all in private subnets)

| Instance | Private IP | Type | Subnet | Role |
|----------|-----------|------|--------|------|
| `codabench-prodlike-app` | `10.0.11.11` | `m6i.4xlarge` | private-1 | Codabench Django app (port 8000) + RabbitMQ broker (port 5672) |
| `codabench-prodlike-nginx-minio` | `10.0.11.12` | `t3.medium` | private-1 | Internal NGINX reverse proxy load-balancing MinIO nodes |
| `codabench-prodlike-minio-1` | `10.0.11.20` | `t3.small` | private-1 | MinIO distributed storage node (2 × 100 GB EBS) |
| `codabench-prodlike-minio-2` | `10.0.11.21` | `t3.small` | private-1 | MinIO distributed storage node |
| `codabench-prodlike-minio-3` | `10.0.11.22` | `t3.small` | private-1 | MinIO distributed storage node |
| `codabench-prodlike-minio-4` | `10.0.11.23` | `t3.small` | private-1 | MinIO distributed storage node |

### Workers (Auto Scaling Group)

| Property | Value |
|----------|-------|
| Name | `codabench-prodlike-workers-asg` |
| Instance type | `c6i.large` |
| Subnets | Both private subnets |
| Min / Desired / Max | 8 / 8 / 15 |
| Role | Consume tasks from RabbitMQ, read/write datasets to MinIO |

### S3

| Bucket | Role |
|--------|------|
| `tf-codabench-backend` | Terraform state backend |
| `codabench-prodlike-*` deploy bucket | Stores Codabench source code, synced to the app instance at boot |

## Security Groups

| SG Name | Attached to | Ingress rules |
|---------|-------------|---------------|
| `codabench-prodlike-alb-sg` | Both ALBs | `0.0.0.0/0` → 80, 443, 9000, 9001 |
| `codabench-prodlike-codabench-sg` | Codabench app | ALB SG → 8000, Workers SG → 5672 |
| `codabench-prodlike-nginx-minio-sg` | NGINX MinIO | Codabench SG → 9000, Workers SG → 9000, ALB SG → 9000/9001 |
| `codabench-prodlike-minio-sg` | MinIO nodes | NGINX SG → 9000/9001, Codabench SG → 9000, Workers SG → 9000, self → 9000 (inter-node) |
| `codabench-prodlike-workers-sg` | Workers ASG | Egress only (no ingress) |

All security groups allow **all egress** (`0.0.0.0/0`, all protocols).

## Access

- **Web UI:** via ALB DNS on port 80 (output: `alb_dns`)
- **Admin/SSH:** via AWS SSM Session Manager — all instances have the
  `codabench-prodlike-ssm-role` IAM role with `AmazonSSMManagedInstanceCore`
- **MinIO Console:** via ALB at path `/minio-console`
- **MinIO API:** via the dedicated MinIO API ALB on port 80

```bash
# Connect to any instance via SSM
aws ssm start-session --target <instance-id> --profile codabench
```

## Terraform Files

| File | Purpose |
|------|---------|
| `provider.tf` | AWS provider config, S3 backend |
| `variables.tf` | All input variables (CIDRs, instance types, credentials, images) |
| `main.tf` | Root module — wires VPC, SGs, EC2, workers, ALBs, NAT gateway |
| `outputs.tf` | ALB DNS, Codabench IPs, MinIO/RabbitMQ endpoints |
| `modules/vpc/` | VPC, subnets, route tables, internet gateway |
| `modules/security_groups/` | All security groups and their rules |
| `modules/ec2/` | Generic EC2 instance module (used by app, NGINX, MinIO) |
| `modules/workers/` | Launch template + Auto Scaling Group for workers |
| `modules/s3_deploy/` | S3 bucket for deploying Codabench source to instances |
| `templates/` | User data scripts (cloud-init) for each instance type |

## Key Terraform References

For anyone adding new infrastructure in this VPC:

```hcl
module.vpc.vpc_id                    # VPC ID
module.vpc.public_subnet_ids         # [subnet-pub-1, subnet-pub-2]
module.vpc.private_subnet_ids        # [subnet-priv-1, subnet-priv-2]
module.vpc.private_route_table_id    # Route table with NAT GW default route
module.security_groups.codabench_sg_id
module.security_groups.alb_sg_id
module.security_groups.workers_sg_id
aws_iam_instance_profile.ssm_instance_profile.name  # Reusable SSM profile
local.codabench_private_ip           # 10.0.11.11
```
