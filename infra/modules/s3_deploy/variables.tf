variable "name_prefix" {
  type        = string
  description = "Prefix used for naming the S3 bucket."
}

variable "source_dir" {
  type        = string
  description = "Local directory whose contents are uploaded to the bucket."
}

variable "s3_prefix" {
  type        = string
  description = "Key prefix (folder) under which files are uploaded in the bucket."
  default     = "codabench"
}

variable "tags" {
  type        = map(string)
  description = "Common tags applied to all resources."
  default     = {}
}
