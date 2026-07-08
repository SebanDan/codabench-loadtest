output "alb_sg_id" {
  description = "ALB SG ID when ALB is enabled."
  value       = var.enable_alb ? aws_security_group.alb[0].id : null
}

output "reverse_proxy_sg_id" {
  description = "Traefik SG ID when ALB is disabled."
  value       = var.enable_alb ? null : aws_security_group.reverse_proxy[0].id
}

output "codabench_sg_id" {
  description = "Codabench SG ID."
  value       = aws_security_group.codabench.id
}

output "minio_sg_id" {
  description = "MinIO SG ID."
  value       = aws_security_group.minio.id
}

output "nginx_minio_sg_id" {
  description = "Internal NGINX SG ID."
  value       = aws_security_group.nginx_minio.id
}

output "workers_sg_id" {
  description = "Workers SG ID."
  value       = aws_security_group.workers.id
}
