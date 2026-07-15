output "bucket_name" {
  description = "Name of the S3 deploy bucket."
  value       = aws_s3_bucket.this.id
}

output "bucket_arn" {
  description = "ARN of the S3 deploy bucket."
  value       = aws_s3_bucket.this.arn
}

output "s3_prefix" {
  description = "Key prefix under which the source files are uploaded."
  value       = var.s3_prefix
}

output "uploaded_object_keys" {
  description = "Keys of all uploaded source objects."
  value       = [for o in aws_s3_object.source : o.key]
}
