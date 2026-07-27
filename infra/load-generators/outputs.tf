output "paris_locust_master_id" {
  description = "Instance ID of the Locust master (for SSM)."
  value       = module.paris.locust_master_id
}

output "paris_locust_master_ip" {
  description = "Private IP of the Locust master."
  value       = module.paris.locust_master_private_ip
}

output "paris_playwright_id" {
  description = "Instance ID of the Playwright instance (for SSM)."
  value       = module.paris.playwright_id
}

output "paris_workers_asg" {
  description = "Name of the Paris Locust workers ASG."
  value       = module.paris.workers_asg_name
}

output "us_east_workers_asg" {
  description = "Name of the US East Locust workers ASG."
  value       = module.us_east.workers_asg_name
}

output "ap_southeast_workers_asg" {
  description = "Name of the AP Southeast Locust workers ASG."
  value       = module.ap_southeast.workers_asg_name
}

output "codabench_alb_dns" {
  description = "DNS of the Codabench ALB (target for remote region tests)."
  value       = module.paris.alb_dns
}

output "codabench_app_ip" {
  description = "Private IP of the Codabench app (target for Paris tests)."
  value       = var.codabench_app_ip
}

output "results_bucket" {
  description = "S3 bucket for collecting results from all regions."
  value       = aws_s3_bucket.results.bucket
}
