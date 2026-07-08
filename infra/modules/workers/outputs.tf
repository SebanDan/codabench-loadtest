output "autoscaling_group_name" {
  description = "Worker ASG name."
  value       = aws_autoscaling_group.this.name
}

output "launch_template_id" {
  description = "Worker launch template ID."
  value       = aws_launch_template.this.id
}
