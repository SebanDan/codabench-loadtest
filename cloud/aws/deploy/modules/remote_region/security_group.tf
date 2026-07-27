resource "aws_security_group" "locust" {
  name        = "${var.name_prefix}-${var.region_name}-locust-sg"
  description = "Locust remote workers (${var.region_name})"
  vpc_id      = aws_vpc.this.id

  tags = {
    Name      = "${var.name_prefix}-${var.region_name}-locust-sg"
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }
}

# Test traffic to ALB Paris (via public internet)
resource "aws_vpc_security_group_egress_rule" "to_alb" {
  security_group_id = aws_security_group.locust.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
  description       = "HTTP to Codabench ALB via internet"
}

# HTTPS for pip install, git clone, S3 upload
resource "aws_vpc_security_group_egress_rule" "to_internet_https" {
  security_group_id = aws_security_group.locust.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  description       = "HTTPS to internet (pip, git, S3)"
}
