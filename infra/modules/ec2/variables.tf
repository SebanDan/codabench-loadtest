variable "name" {
  type        = string
  description = "Name for the EC2 instance resource."
}

variable "ami_id" {
  type        = string
  description = "AMI ID used by the instance."
}

variable "instance_type" {
  type        = string
  description = "EC2 instance type."
}

variable "subnet_id" {
  type        = string
  description = "Subnet where instance is launched."
}

variable "security_group_ids" {
  type        = list(string)
  description = "Security groups attached to the instance."
}

variable "key_name" {
  type        = string
  description = "Optional EC2 key pair name."
  default     = null
}

variable "iam_instance_profile_name" {
  type        = string
  description = "Optional IAM instance profile name for EC2 instance."
  default     = null
}

variable "associate_public_ip" {
  type        = bool
  description = "Assign a public IPv4 address."
  default     = false
}

variable "private_ip" {
  type        = string
  description = "Optional static private IP."
  default     = null
}

variable "root_volume_size" {
  type        = number
  description = "Root volume size in GiB."
  default     = 20
}

variable "root_volume_type" {
  type        = string
  description = "Root volume type."
  default     = "gp3"
}

variable "additional_ebs_block_devices" {
  type = list(object({
    device_name = string
    volume_size = number
    volume_type = string
    encrypted   = bool
  }))
  description = "Optional additional EBS block devices attached to the instance."
  default     = []
}

variable "user_data" {
  type        = string
  description = "Cloud-init user data script."
  default     = ""
}

variable "source_dest_check" {
  type        = bool
  description = "Enable source/destination checks."
  default     = true
}

variable "tags" {
  type        = map(string)
  description = "Tags applied to instance resources."
  default     = {}
}
