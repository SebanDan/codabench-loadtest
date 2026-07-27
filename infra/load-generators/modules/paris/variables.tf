terraform {
  required_providers {
    aws = {
      source = "hashicorp/aws"
    }
  }
}

variable "name_prefix" {
  type = string
}

variable "codabench_vpc_name" {
  type = string
}

variable "codabench_private_rt_name" {
  type = string
}

variable "codabench_alb_name" {
  type = string
}

variable "codabench_alb_sg_name" {
  type = string
}

variable "codabench_app_sg_name" {
  type = string
}

variable "locust_subnet_cidr" {
  type = string
}

variable "locust_subnet_az" {
  type = string
}

variable "master_instance_type" {
  type = string
}

variable "worker_instance_type" {
  type = string
}

variable "playwright_instance_type" {
  type = string
}

variable "worker_min_size" {
  type = number
}

variable "worker_max_size" {
  type = number
}

variable "worker_desired_capacity" {
  type = number
}

variable "iam_instance_profile_name" {
  type = string
}

variable "repo_url" {
  type = string
}

variable "repo_branch" {
  type = string
}

variable "results_bucket" {
  type = string
}

variable "codabench_app_ip" {
  description = "Private IP of the Codabench app instance"
  type        = string
}

variable "codabench_rabbitmq_user" {
  type = string
}

variable "codabench_rabbitmq_password" {
  type      = string
  sensitive = true
}

variable "codabench_username" {
  type = string
}

variable "codabench_password" {
  type      = string
  sensitive = true
}
