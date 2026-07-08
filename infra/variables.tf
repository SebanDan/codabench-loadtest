variable "aws_region" {
  type        = string
  description = "AWS region for deployment."
  default     = "eu-west-1"
}

variable "aws_profile" {
  type        = string
  description = "AWS named profile used by provider."
  default     = "codabench"
}

variable "project_name" {
  type        = string
  description = "Project name used in resource naming."
  default     = "codabench"
}

variable "environment" {
  type        = string
  description = "Environment label."
  default     = "prodlike"
}

variable "ami_id" {
  type        = string
  description = "Pinned AMI ID for EC2 instances to avoid automatic replacement when a newer AMI is published."
  default     = "ami-05af3290611073bb6"
}

variable "key_name" {
  type        = string
  description = "Optional key pair for SSH access."
  default     = null
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for VPC."
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "CIDRs for public entry subnets."
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  type        = list(string)
  description = "CIDRs for private backend subnets."
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "availability_zones" {
  type        = list(string)
  description = "AZs used by public and private subnets."
  default     = ["eu-west-1a", "eu-west-1b"]
}

variable "enable_alb" {
  type        = bool
  description = "Use ALB as entry point. If false, deploy Traefik EC2 entrypoint."
  default     = true
}

variable "codabench_port" {
  type        = number
  description = "Codabench app container port."
  default     = 8000
}

variable "codabench_instance_type" {
  type        = string
  description = "Codabench app node instance type."
  default     = "m6i.4xlarge"
}

variable "minio_instance_type" {
  type        = string
  description = "MinIO node instance type."
  default     = "t3.small"
}

variable "nginx_instance_type" {
  type        = string
  description = "NGINX load balancer instance type."
  default     = "t3.medium"
}

variable "traefik_instance_type" {
  type        = string
  description = "Traefik reverse proxy instance type when ALB is disabled."
  default     = "t3.medium"
}

variable "worker_instance_type" {
  type        = string
  description = "Worker ASG instance type."
  default     = "c6i.large"
}

variable "worker_min_size" {
  type        = number
  description = "Worker ASG minimum size."
  default     = 8
}

variable "worker_max_size" {
  type        = number
  description = "Worker ASG maximum size."
  default     = 15
}

variable "worker_desired_capacity" {
  type        = number
  description = "Worker ASG desired size."
  default     = 8
}

variable "minio_node_count" {
  type        = number
  description = "Number of MinIO nodes for distributed setup (2 to 4)."
  default     = 4

  validation {
    condition     = var.minio_node_count >= 2 && var.minio_node_count <= 4
    error_message = "minio_node_count must be between 2 and 4."
  }
}

variable "rabbitmq_user" {
  type        = string
  description = "RabbitMQ default username."
  default     = "rabbit-username"
}

variable "rabbitmq_password" {
  type        = string
  description = "RabbitMQ default password."
  default     = "rabbit-password-you-should-change"
  sensitive   = true
}

variable "minio_access_key" {
  type        = string
  description = "MinIO root access key."
  default     = "testkey"
}

variable "minio_secret_key" {
  type        = string
  description = "MinIO root secret key."
  default     = "secretkey"
  sensitive   = true
}

variable "codabench_image" {
  type        = string
  description = "Container image for Codabench application."
  default     = "codabench/codabench:latest"
}

variable "worker_image" {
  type        = string
  description = "Container image for Codabench worker."
  default     = "codalab/codabench-compute-worker:latest"
}

variable "rabbitmq_image" {
  type        = string
  description = "Container image for RabbitMQ running on Codabench node."
  default     = "rabbitmq:3.13-management"
}
