variable "name_prefix" {
  type        = string
  description = "Prefix for security group names."
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where security groups are created."
}

variable "codabench_port" {
  type        = number
  description = "Port exposed by Codabench app container."
  default     = 8000
}

variable "enable_alb" {
  type        = bool
  description = "Whether ALB is used as entry point."
}

variable "tags" {
  type        = map(string)
  description = "Common tags for security groups."
  default     = {}
}
