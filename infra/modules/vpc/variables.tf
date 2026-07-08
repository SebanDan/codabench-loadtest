variable "name_prefix" {
  type        = string
  description = "Prefix used for naming VPC resources."
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC."
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for public subnets."
}

variable "private_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for private subnets."
}

variable "azs" {
  type        = list(string)
  description = "Availability zones used for subnets."
}

variable "tags" {
  type        = map(string)
  description = "Common tags applied to all resources."
  default     = {}
}
