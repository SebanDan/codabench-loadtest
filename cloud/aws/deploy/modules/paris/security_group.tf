resource "aws_security_group" "locust" {
  name        = "${var.name_prefix}-locust-sg"
  description = "Locust load generators (Paris)"
  vpc_id      = data.aws_vpc.codabench.id

  tags = {
    Name      = "${var.name_prefix}-locust-sg"
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }
}

# --- Egress rules ---

# Test traffic: Locust -> ALB on port 80
resource "aws_vpc_security_group_egress_rule" "to_alb" {
  security_group_id            = aws_security_group.locust.id
  referenced_security_group_id = data.aws_security_group.alb.id
  from_port                    = 80
  to_port                      = 80
  ip_protocol                  = "tcp"
  description                  = "Load test traffic to ALB"
}

# Test traffic: Locust -> Codabench Caddy on port 80 (direct, no ALB hairpin)
resource "aws_vpc_security_group_egress_rule" "to_codabench_http" {
  security_group_id            = aws_security_group.locust.id
  referenced_security_group_id = data.aws_security_group.codabench.id
  from_port                    = 80
  to_port                      = 80
  ip_protocol                  = "tcp"
  description                  = "Load test traffic to Codabench (direct)"
}

# Monitoring: Locust -> Codabench RabbitMQ Management on port 15672
resource "aws_vpc_security_group_egress_rule" "to_rabbitmq" {
  security_group_id            = aws_security_group.locust.id
  referenced_security_group_id = data.aws_security_group.codabench.id
  from_port                    = 15672
  to_port                      = 15672
  ip_protocol                  = "tcp"
  description                  = "RabbitMQ management API monitoring"
}

# Internet access via NAT: pip install, git clone
resource "aws_vpc_security_group_egress_rule" "to_internet" {
  security_group_id = aws_security_group.locust.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  description       = "HTTPS to internet via NAT (pip, git)"
}

# --- Ingress rules ---

# Locust master web UI (port 8089) — only from within the Locust subnet
resource "aws_vpc_security_group_ingress_rule" "master_ui" {
  security_group_id = aws_security_group.locust.id
  cidr_ipv4         = var.locust_subnet_cidr
  from_port         = 8089
  to_port           = 8089
  ip_protocol       = "tcp"
  description       = "Locust master web UI (SSM port forwarding)"
}

# Locust master ← workers (internal protocol)
resource "aws_vpc_security_group_ingress_rule" "master_workers" {
  security_group_id            = aws_security_group.locust.id
  referenced_security_group_id = aws_security_group.locust.id
  from_port                    = 5557
  to_port                      = 5558
  ip_protocol                  = "tcp"
  description                  = "Locust master-worker communication"
}

# Locust master ← remote workers via NLB (public internet)
resource "aws_vpc_security_group_ingress_rule" "master_workers_nlb" {
  security_group_id = aws_security_group.locust.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 5557
  to_port           = 5558
  ip_protocol       = "tcp"
  description       = "Locust master-worker via NLB (remote regions)"
}

# --- Rules on EXISTING SGs: allow Locust traffic in ---

resource "aws_vpc_security_group_ingress_rule" "alb_from_locust" {
  security_group_id            = data.aws_security_group.alb.id
  referenced_security_group_id = aws_security_group.locust.id
  from_port                    = 80
  to_port                      = 80
  ip_protocol                  = "tcp"
  description                  = "Locust load test traffic to ALB"
}

resource "aws_vpc_security_group_ingress_rule" "codabench_http_from_locust" {
  security_group_id            = data.aws_security_group.codabench.id
  referenced_security_group_id = aws_security_group.locust.id
  from_port                    = 80
  to_port                      = 80
  ip_protocol                  = "tcp"
  description                  = "Locust load test traffic to Caddy/Django"
}

resource "aws_vpc_security_group_ingress_rule" "codabench_rabbitmq_from_locust" {
  security_group_id            = data.aws_security_group.codabench.id
  referenced_security_group_id = aws_security_group.locust.id
  from_port                    = 15672
  to_port                      = 15672
  ip_protocol                  = "tcp"
  description                  = "Locust monitoring to RabbitMQ Management"
}
