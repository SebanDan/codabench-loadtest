output "vpc_id" {
  value = aws_vpc.this.id
}

output "subnet_id" {
  value = aws_subnet.public.id
}

output "workers_asg_name" {
  value = aws_autoscaling_group.locust_workers.name
}

output "security_group_id" {
  value = aws_security_group.locust.id
}
