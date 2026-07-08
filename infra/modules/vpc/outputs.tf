output "vpc_id" {
  description = "VPC ID."
  value       = aws_vpc.this.id
}

output "vpc_cidr" {
  description = "VPC CIDR block."
  value       = aws_vpc.this.cidr_block
}

output "public_subnet_ids" {
  description = "Public subnet IDs."
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs."
  value       = aws_subnet.private[*].id
}

output "private_subnet_cidrs" {
  description = "Private subnet CIDRs."
  value       = aws_subnet.private[*].cidr_block
}

output "private_route_table_id" {
  description = "Private route table ID."
  value       = aws_route_table.private.id
}
