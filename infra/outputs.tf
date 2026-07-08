output "alb_dns" {
  description = "ALB DNS name when ALB is enabled."
  value       = var.enable_alb ? aws_lb.entry[0].dns_name : null
}

output "codabench_public_ip" {
  description = "Codabench public IP (null when running in private subnet)."
  value       = module.codabench.public_ip
}

output "codabench_private_ip" {
  description = "Codabench private IP."
  value       = module.codabench.private_ip
}

output "rabbitmq_internal_endpoint" {
  description = "RabbitMQ endpoint for internal workloads (hosted on Codabench instance)."
  value       = "${module.codabench.private_ip}:5672"
}

output "minio_endpoint" {
  description = "Client-facing MinIO API endpoint (path-based when ALB is enabled)."
  value       = local.minio_endpoint
}

output "minio_console_endpoint" {
  description = "Client-facing MinIO Console endpoint (path-based when ALB is enabled)."
  value       = local.minio_console_endpoint
}
