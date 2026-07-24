output "locust_master_id" {
  value = aws_instance.locust_master.id
}

output "locust_master_private_ip" {
  value = aws_instance.locust_master.private_ip
}

output "playwright_id" {
  value = aws_instance.playwright.id
}

output "playwright_private_ip" {
  value = aws_instance.playwright.private_ip
}

output "workers_asg_name" {
  value = aws_autoscaling_group.locust_workers.name
}

output "locust_subnet_id" {
  value = aws_subnet.locust.id
}

output "alb_dns" {
  value = data.aws_lb.codabench.dns_name
}
