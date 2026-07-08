output "id" {
  description = "Instance ID."
  value       = aws_instance.this.id
}

output "private_ip" {
  description = "Instance private IP."
  value       = aws_instance.this.private_ip
}

output "public_ip" {
  description = "Instance public IP."
  value       = aws_instance.this.public_ip
}
