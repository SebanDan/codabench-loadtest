variable "name_prefix" {
  type        = string
  description = "Prefix used to name worker resources."
}

variable "ami_id" {
  type        = string
  description = "AMI ID for worker instances."
}

variable "instance_type" {
  type        = string
  description = "Worker instance type."
}

variable "subnet_ids" {
  type        = list(string)
  description = "Subnets used by the Auto Scaling Group."
}

variable "security_group_ids" {
  type        = list(string)
  description = "Security groups for worker instances."
}

variable "key_name" {
  type        = string
  description = "Optional EC2 key pair name."
  default     = null
}

variable "iam_instance_profile_name" {
  type        = string
  description = "Optional IAM instance profile name for worker instances."
  default     = null
}

variable "min_size" {
  type        = number
  description = "ASG minimum capacity."
}

variable "max_size" {
  type        = number
  description = "ASG maximum capacity."
}

variable "desired_capacity" {
  type        = number
  description = "ASG desired capacity."
}

variable "user_data" {
  type        = string
  description = "Worker user data script."
}

variable "root_volume_size" {
  type        = number
  description = "Root volume size in GiB."
  default     = 50
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to worker resources."
  default     = {}
}
