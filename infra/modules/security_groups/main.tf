resource "aws_security_group" "alb" {
  count = var.enable_alb ? 1 : 0

  name        = "${var.name_prefix}-alb-sg"
  description = "Public ingress for ALB"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-alb-sg"
  })
}

resource "aws_vpc_security_group_ingress_rule" "alb_http" {
  count = var.enable_alb ? 1 : 0

  security_group_id = aws_security_group.alb[0].id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
  description       = "HTTP ingress"
}

resource "aws_vpc_security_group_ingress_rule" "alb_https" {
  count = var.enable_alb ? 1 : 0

  security_group_id = aws_security_group.alb[0].id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  to_port           = 443
  ip_protocol       = "tcp"
  description       = "HTTPS ingress"
}

resource "aws_vpc_security_group_ingress_rule" "alb_minio_http" {
  count = var.enable_alb ? 1 : 0

  security_group_id = aws_security_group.alb[0].id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 9000
  to_port           = 9000
  ip_protocol       = "tcp"
  description       = "MinIO HTTP ingress"
}

resource "aws_vpc_security_group_ingress_rule" "alb_minio_console_http" {
  count = var.enable_alb ? 1 : 0

  security_group_id = aws_security_group.alb[0].id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 9001
  to_port           = 9001
  ip_protocol       = "tcp"
  description       = "MinIO Console HTTP ingress"
}

resource "aws_vpc_security_group_egress_rule" "alb_egress" {
  count = var.enable_alb ? 1 : 0

  security_group_id = aws_security_group.alb[0].id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all egress"
}

resource "aws_security_group" "reverse_proxy" {
  count = var.enable_alb ? 0 : 1

  name        = "${var.name_prefix}-traefik-sg"
  description = "Public ingress for Traefik reverse proxy"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-traefik-sg"
  })
}

resource "aws_vpc_security_group_ingress_rule" "reverse_proxy_http" {
  count = var.enable_alb ? 0 : 1

  security_group_id = aws_security_group.reverse_proxy[0].id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  to_port           = 80
  ip_protocol       = "tcp"
  description       = "HTTP ingress"
}

resource "aws_vpc_security_group_egress_rule" "reverse_proxy_egress" {
  count = var.enable_alb ? 0 : 1

  security_group_id = aws_security_group.reverse_proxy[0].id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all egress"
}

resource "aws_security_group" "codabench" {
  name        = "${var.name_prefix}-codabench-sg"
  description = "Codabench app security group"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-codabench-sg"
  })
}

resource "aws_vpc_security_group_ingress_rule" "codabench_from_alb" {
  count = var.enable_alb ? 1 : 0

  security_group_id            = aws_security_group.codabench.id
  referenced_security_group_id = aws_security_group.alb[0].id
  from_port                    = var.codabench_port
  to_port                      = var.codabench_port
  ip_protocol                  = "tcp"
  description                  = "ALB to Codabench"
}

resource "aws_vpc_security_group_ingress_rule" "codabench_from_reverse_proxy" {
  count = var.enable_alb ? 0 : 1

  security_group_id            = aws_security_group.codabench.id
  referenced_security_group_id = aws_security_group.reverse_proxy[0].id
  from_port                    = var.codabench_port
  to_port                      = var.codabench_port
  ip_protocol                  = "tcp"
  description                  = "Traefik to Codabench"
}

resource "aws_vpc_security_group_ingress_rule" "codabench_rabbitmq_from_workers" {
  security_group_id            = aws_security_group.codabench.id
  referenced_security_group_id = aws_security_group.workers.id
  from_port                    = 5672
  to_port                      = 5672
  ip_protocol                  = "tcp"
  description                  = "Workers to RabbitMQ on Codabench"
}

resource "aws_vpc_security_group_egress_rule" "codabench_egress" {
  security_group_id = aws_security_group.codabench.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all egress"
}

resource "aws_security_group" "minio" {
  name        = "${var.name_prefix}-minio-sg"
  description = "MinIO nodes SG"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-minio-sg"
  })
}

resource "aws_security_group" "nginx_minio" {
  name        = "${var.name_prefix}-nginx-minio-sg"
  description = "Internal NGINX LB for MinIO"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-nginx-minio-sg"
  })
}

resource "aws_security_group" "workers" {
  name        = "${var.name_prefix}-workers-sg"
  description = "Codabench workers SG"
  vpc_id      = var.vpc_id

  tags = merge(var.tags, {
    Name = "${var.name_prefix}-workers-sg"
  })
}

resource "aws_vpc_security_group_ingress_rule" "nginx_from_codabench" {
  security_group_id            = aws_security_group.nginx_minio.id
  referenced_security_group_id = aws_security_group.codabench.id
  from_port                    = 9000
  to_port                      = 9000
  ip_protocol                  = "tcp"
  description                  = "Codabench to MinIO endpoint"
}

resource "aws_vpc_security_group_ingress_rule" "nginx_from_workers" {
  security_group_id            = aws_security_group.nginx_minio.id
  referenced_security_group_id = aws_security_group.workers.id
  from_port                    = 9000
  to_port                      = 9000
  ip_protocol                  = "tcp"
  description                  = "Workers to MinIO endpoint"
}

resource "aws_vpc_security_group_ingress_rule" "nginx_from_alb_minio" {
  count = var.enable_alb ? 1 : 0

  security_group_id            = aws_security_group.nginx_minio.id
  referenced_security_group_id = aws_security_group.alb[0].id
  from_port                    = 9000
  to_port                      = 9000
  ip_protocol                  = "tcp"
  description                  = "ALB to MinIO endpoint"
}

resource "aws_vpc_security_group_ingress_rule" "nginx_from_alb_minio_console" {
  count = var.enable_alb ? 1 : 0

  security_group_id            = aws_security_group.nginx_minio.id
  referenced_security_group_id = aws_security_group.alb[0].id
  from_port                    = 9001
  to_port                      = 9001
  ip_protocol                  = "tcp"
  description                  = "ALB to MinIO Console endpoint"
}

resource "aws_vpc_security_group_egress_rule" "nginx_egress" {
  security_group_id = aws_security_group.nginx_minio.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all egress"
}

resource "aws_vpc_security_group_ingress_rule" "minio_from_nginx" {
  security_group_id            = aws_security_group.minio.id
  referenced_security_group_id = aws_security_group.nginx_minio.id
  from_port                    = 9000
  to_port                      = 9000
  ip_protocol                  = "tcp"
  description                  = "NGINX to MinIO"
}

resource "aws_vpc_security_group_ingress_rule" "minio_console_from_nginx" {
  security_group_id            = aws_security_group.minio.id
  referenced_security_group_id = aws_security_group.nginx_minio.id
  from_port                    = 9001
  to_port                      = 9001
  ip_protocol                  = "tcp"
  description                  = "NGINX to MinIO Console"
}

resource "aws_vpc_security_group_ingress_rule" "minio_console_from_alb" {
  count = var.enable_alb ? 1 : 0

  security_group_id            = aws_security_group.minio.id
  referenced_security_group_id = aws_security_group.alb[0].id
  from_port                    = 9001
  to_port                      = 9001
  ip_protocol                  = "tcp"
  description                  = "ALB to MinIO Console"
}

resource "aws_vpc_security_group_ingress_rule" "minio_from_codabench" {
  security_group_id            = aws_security_group.minio.id
  referenced_security_group_id = aws_security_group.codabench.id
  from_port                    = 9000
  to_port                      = 9000
  ip_protocol                  = "tcp"
  description                  = "Codabench direct to MinIO"
}

resource "aws_vpc_security_group_ingress_rule" "minio_from_workers" {
  security_group_id            = aws_security_group.minio.id
  referenced_security_group_id = aws_security_group.workers.id
  from_port                    = 9000
  to_port                      = 9000
  ip_protocol                  = "tcp"
  description                  = "Workers direct to MinIO"
}

resource "aws_vpc_security_group_ingress_rule" "minio_inter_node" {
  security_group_id            = aws_security_group.minio.id
  referenced_security_group_id = aws_security_group.minio.id
  from_port                    = 9000
  to_port                      = 9000
  ip_protocol                  = "tcp"
  description                  = "MinIO node-to-node"
}

resource "aws_vpc_security_group_egress_rule" "minio_egress" {
  security_group_id = aws_security_group.minio.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all egress"
}

resource "aws_vpc_security_group_egress_rule" "workers_egress" {
  security_group_id = aws_security_group.workers.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"
  description       = "Allow all egress"
}
