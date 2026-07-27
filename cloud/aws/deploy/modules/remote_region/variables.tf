variable "name_prefix" {
  type = string
}

variable "region_name" {
  description = "Short region label (us-east, ap-southeast)."
  type        = string
}

variable "vpc_cidr" {
  type = string
}

variable "subnet_cidr" {
  description = "Public subnet CIDR for this region."
  type        = string
  default     = null
}

variable "subnet_az_index" {
  description = "Index of the AZ to use (0 = first AZ in the region)."
  type        = number
  default     = 0
}

variable "worker_instance_type" {
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

variable "alb_dns" {
  description = "Public DNS of the Codabench ALB in Paris."
  type        = string
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

variable "codabench_username" {
  type = string
}

variable "codabench_password" {
  type      = string
  sensitive = true
}
