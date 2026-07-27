variable "aws_profile" {
  type    = string
  default = "codabench"
}

variable "name_prefix" {
  type    = string
  default = "codabench-loadtest"
}

# --- Existing Codabench infra references (Paris) ---

variable "codabench_vpc_name" {
  type    = string
  default = "codabench-prodlike-vpc"
}

variable "codabench_private_rt_name" {
  type    = string
  default = "codabench-prodlike-private-rt"
}

variable "codabench_alb_name" {
  type    = string
  default = "codabench-prodlike-alb"
}

variable "codabench_alb_sg_name" {
  type    = string
  default = "codabench-prodlike-alb-sg"
}

variable "codabench_app_sg_name" {
  type    = string
  default = "codabench-prodlike-codabench-sg"
}

variable "codabench_iam_profile_name" {
  type    = string
  default = "codabench-prodlike-ssm-instance-profile"
}

variable "codabench_app_ip" {
  description = "Private IP of the Codabench app instance (Django/Caddy/RabbitMQ)"
  type        = string
  default     = "10.0.11.11"
}

# --- Paris Locust subnet ---

variable "paris_locust_subnet_cidr" {
  type    = string
  default = "10.0.21.0/24"
}

variable "paris_locust_subnet_az" {
  type    = string
  default = "eu-west-1a"
}

# --- Remote region VPC CIDRs ---

variable "us_east_vpc_cidr" {
  type    = string
  default = "10.1.0.0/16"
}

variable "ap_southeast_vpc_cidr" {
  type    = string
  default = "10.2.0.0/16"
}

# --- Instance sizing ---

variable "master_instance_type" {
  type    = string
  default = "t3.medium"
}

variable "worker_instance_type" {
  type    = string
  default = "t3.medium"
}

variable "playwright_instance_type" {
  type    = string
  default = "t3.large"
}

# --- Paris ASG ---

variable "paris_worker_min" {
  type    = number
  default = 2
}

variable "paris_worker_max" {
  type    = number
  default = 6
}

variable "paris_worker_desired" {
  type    = number
  default = 2
}

# --- US East ASG ---

variable "us_east_worker_min" {
  type    = number
  default = 2
}

variable "us_east_worker_max" {
  type    = number
  default = 4
}

variable "us_east_worker_desired" {
  type    = number
  default = 2
}

# --- AP Southeast ASG ---

variable "ap_southeast_worker_min" {
  type    = number
  default = 2
}

variable "ap_southeast_worker_max" {
  type    = number
  default = 4
}

variable "ap_southeast_worker_desired" {
  type    = number
  default = 2
}

# --- App config ---

variable "loadtest_repo_url" {
  type    = string
  default = "https://github.com/SebanDan/codabench-loadtest.git"
}

variable "loadtest_repo_branch" {
  type    = string
  default = "main"
}

# --- S3 results bucket ---

variable "results_bucket_name" {
  type    = string
  default = "codabench-loadtest-results"
}
