locals {
  name_prefix     = "${var.project_name}-${var.environment}"
  selected_ami_id = coalesce(var.ami_id, data.aws_ami.amazon_linux_2023.id)

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }

  codabench_private_ip = cidrhost(var.private_subnet_cidrs[0], 11)
  nginx_private_ip     = cidrhost(var.private_subnet_cidrs[0], 12)
  minio_private_ips = [
    for i in range(var.minio_node_count) : cidrhost(var.private_subnet_cidrs[0], 20 + i)
  ]

  minio_cluster_targets          = join(" ", flatten([for ip in local.minio_private_ips : ["http://${ip}/data1", "http://${ip}/data2"]]))
  nginx_upstream_servers         = join("\n", [for ip in local.minio_private_ips : "  server ${ip}:9000;"])
  nginx_console_upstream_servers = join("\n", [for ip in local.minio_private_ips : "  server ${ip}:9001;"])

  codabench_broker_url            = "amqp://${var.rabbitmq_user}:${var.rabbitmq_password}@127.0.0.1:5672/"
  workers_broker_url              = "amqp://68730128-9c70-4f35-9537-b0a388589802:b41eb27e-43b5-4c90-af22-57c452e1cc8d@codabench-prodlike-alb-1404037449.eu-west-1.elb.amazonaws.com:5672/d6757654-20f1-42c8-b8f6-7298facd111d"
  minio_internal_endpoint         = "http://${local.nginx_private_ip}:9000"
  minio_internal_console_endpoint = "http://${local.nginx_private_ip}:9001"
  minio_endpoint                  = var.enable_alb ? "http://${aws_lb.minio_api_entry[0].dns_name}" : local.minio_internal_endpoint
  minio_console_endpoint          = var.enable_alb ? "http://${aws_lb.entry[0].dns_name}/minio-console" : local.minio_internal_console_endpoint
}

data "aws_ami" "amazon_linux_2023" {
  most_recent = true
  owners      = ["amazon"]

  filter {
    name   = "name"
    values = ["al2023-ami-2023.*-x86_64"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }

  filter {
    name   = "root-device-type"
    values = ["ebs"]
  }
}

data "aws_iam_policy_document" "ec2_assume_role" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "ssm_instance_role" {
  name               = "${local.name_prefix}-ssm-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ssm-role"
  })
}

resource "aws_iam_role_policy_attachment" "ssm_managed_instance_core" {
  role       = aws_iam_role.ssm_instance_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "codabench_s3_read" {
  name = "${local.name_prefix}-codabench-s3-read"
  role = aws_iam_role.ssm_instance_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = ["s3:GetObject", "s3:ListBucket"]
      Resource = [
        module.s3_deploy.bucket_arn,
        "${module.s3_deploy.bucket_arn}/*",
      ]
    }]
  })
}

resource "aws_iam_instance_profile" "ssm_instance_profile" {
  name = "${local.name_prefix}-ssm-instance-profile"
  role = aws_iam_role.ssm_instance_role.name

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ssm-instance-profile"
  })
}

module "vpc" {
  source = "./modules/vpc"

  name_prefix          = local.name_prefix
  vpc_cidr             = var.vpc_cidr
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs
  azs                  = var.availability_zones
  tags                 = local.common_tags
}

module "s3_deploy" {
  source = "./modules/s3_deploy"

  name_prefix = local.name_prefix
  source_dir  = "${path.module}/codabench"
  s3_prefix   = local.name_prefix
  tags        = local.common_tags
}

module "security_groups" {
  source = "./modules/security_groups"

  name_prefix    = local.name_prefix
  vpc_id         = module.vpc.vpc_id
  codabench_port = var.codabench_port
  enable_alb     = var.enable_alb
  tags           = local.common_tags
}

resource "aws_eip" "nat" {
  domain = "vpc"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-nat-eip"
  })
}

resource "aws_nat_gateway" "this" {
  allocation_id = aws_eip.nat.id
  subnet_id     = module.vpc.public_subnet_ids[0]

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-nat-gw"
  })
}

resource "aws_route" "private_default" {
  route_table_id         = module.vpc.private_route_table_id
  destination_cidr_block = "0.0.0.0/0"
  nat_gateway_id         = aws_nat_gateway.this.id
}

module "minio_nodes" {
  source = "./modules/ec2"
  count  = var.minio_node_count

  name                      = "${local.name_prefix}-minio-${count.index + 1}"
  ami_id                    = local.selected_ami_id
  instance_type             = var.minio_instance_type
  subnet_id                 = module.vpc.private_subnet_ids[0]
  security_group_ids        = [module.security_groups.minio_sg_id]
  key_name                  = var.key_name
  iam_instance_profile_name = aws_iam_instance_profile.ssm_instance_profile.name
  associate_public_ip       = false
  private_ip                = local.minio_private_ips[count.index]
  root_volume_size          = 200
  additional_ebs_block_devices = [
    {
      device_name = "/dev/sdf"
      volume_size = 100
      volume_type = "gp3"
      encrypted   = true
    },
    {
      device_name = "/dev/sdg"
      volume_size = 100
      volume_type = "gp3"
      encrypted   = true
    }
  ]
  user_data = templatefile("${path.module}/templates/minio.sh.tftpl", {
    minio_access_key      = var.minio_access_key
    minio_secret_key      = var.minio_secret_key
    minio_cluster_targets = local.minio_cluster_targets
  })
  tags = local.common_tags

  depends_on = [aws_route.private_default]
}

module "nginx_minio" {
  source = "./modules/ec2"

  name                      = "${local.name_prefix}-nginx-minio"
  ami_id                    = local.selected_ami_id
  instance_type             = var.nginx_instance_type
  subnet_id                 = module.vpc.private_subnet_ids[0]
  security_group_ids        = [module.security_groups.nginx_minio_sg_id]
  key_name                  = var.key_name
  iam_instance_profile_name = aws_iam_instance_profile.ssm_instance_profile.name
  associate_public_ip       = false
  private_ip                = local.nginx_private_ip
  root_volume_size          = 50
  user_data = templatefile("${path.module}/templates/nginx-minio-lb.sh.tftpl", {
    nginx_upstream_servers         = local.nginx_upstream_servers
    nginx_console_upstream_servers = local.nginx_console_upstream_servers
  })
  tags = local.common_tags

  depends_on = [module.minio_nodes]
}

module "codabench" {
  source = "./modules/ec2"

  name                      = "${local.name_prefix}-app"
  ami_id                    = local.selected_ami_id
  instance_type             = var.codabench_instance_type
  subnet_id                 = module.vpc.private_subnet_ids[0]
  security_group_ids        = [module.security_groups.codabench_sg_id]
  key_name                  = var.key_name
  iam_instance_profile_name = aws_iam_instance_profile.ssm_instance_profile.name
  associate_public_ip       = false
  private_ip                = local.codabench_private_ip
  root_volume_size          = 200
  user_data = templatefile("${path.module}/templates/codabench.sh.tftpl", {
    codabench_deploy_bucket = module.s3_deploy.bucket_name
    codabench_deploy_prefix = local.name_prefix
  })
  tags = local.common_tags

  depends_on = [module.nginx_minio, module.s3_deploy]
}

module "workers" {
  source = "./modules/workers"

  name_prefix               = "${local.name_prefix}-workers"
  ami_id                    = local.selected_ami_id
  instance_type             = var.worker_instance_type
  subnet_ids                = module.vpc.private_subnet_ids
  security_group_ids        = [module.security_groups.workers_sg_id]
  key_name                  = var.key_name
  iam_instance_profile_name = aws_iam_instance_profile.ssm_instance_profile.name
  min_size                  = var.worker_min_size
  max_size                  = var.worker_max_size
  desired_capacity          = var.worker_desired_capacity
  user_data = templatefile("${path.module}/templates/worker.sh.tftpl", {
    broker_url   = local.workers_broker_url
    worker_image = var.worker_image
  })
  root_volume_size = 100
  tags             = local.common_tags

  depends_on = [module.codabench, module.nginx_minio]
}

resource "aws_lb" "entry" {
  count = var.enable_alb ? 1 : 0

  name               = substr(replace("${local.name_prefix}-alb", "_", "-"), 0, 32)
  internal           = false
  load_balancer_type = "application"
  security_groups    = [module.security_groups.alb_sg_id]
  subnets            = module.vpc.public_subnet_ids

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-alb"
  })
}

resource "aws_lb" "minio_api_entry" {
  count = var.enable_alb ? 1 : 0

  name               = substr(replace("${local.name_prefix}-minio-api-alb", "_", "-"), 0, 32)
  internal           = false
  load_balancer_type = "application"
  security_groups    = [module.security_groups.alb_sg_id]
  subnets            = module.vpc.public_subnet_ids

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-minio-api-alb"
  })
}

resource "aws_lb_target_group" "codabench" {
  count = var.enable_alb ? 1 : 0

  name        = substr(replace("${local.name_prefix}-cb-tg", "_", "-"), 0, 32)
  port        = var.codabench_port
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = module.vpc.vpc_id

  health_check {
    enabled             = true
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200-499"
    path                = "/"
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-cb-tg"
  })
}

resource "aws_lb_target_group" "minio" {
  count = var.enable_alb ? 1 : 0

  name        = substr(replace("${local.name_prefix}-minio-tg", "_", "-"), 0, 32)
  port        = 9000
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = module.vpc.vpc_id

  health_check {
    enabled             = true
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200"
    path                = "/minio/health/live"
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-minio-tg"
  })
}

resource "aws_lb_target_group" "minio_console" {
  count = var.enable_alb ? 1 : 0

  name        = substr(replace("${local.name_prefix}-minio-ui-tg", "_", "-"), 0, 32)
  port        = 9001
  protocol    = "HTTP"
  target_type = "instance"
  vpc_id      = module.vpc.vpc_id

  health_check {
    enabled             = true
    interval            = 30
    healthy_threshold   = 2
    unhealthy_threshold = 3
    matcher             = "200-399"
    path                = "/minio-console/"
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-minio-pub-ui"
  })
}

resource "aws_lb_target_group_attachment" "codabench" {
  count = var.enable_alb ? 1 : 0

  target_group_arn = aws_lb_target_group.codabench[0].arn
  target_id        = module.codabench.id
  port             = var.codabench_port
}

resource "aws_lb_target_group_attachment" "minio" {
  count = var.enable_alb ? 1 : 0

  target_group_arn = aws_lb_target_group.minio[0].arn
  target_id        = module.nginx_minio.id
  port             = 9000
}

resource "aws_lb_target_group_attachment" "minio_console" {
  count = var.enable_alb ? 1 : 0

  target_group_arn = aws_lb_target_group.minio_console[0].arn
  target_id        = module.nginx_minio.id
  port             = 9001
}

resource "aws_lb_listener" "http" {
  count = var.enable_alb ? 1 : 0

  load_balancer_arn = aws_lb.entry[0].arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.codabench[0].arn
  }
}

resource "aws_lb_listener" "minio_api_http" {
  count = var.enable_alb ? 1 : 0

  load_balancer_arn = aws_lb.minio_api_entry[0].arn
  port              = 80
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.minio[0].arn
  }
}

resource "aws_lb_listener_rule" "minio_console_path" {
  count = var.enable_alb ? 1 : 0

  listener_arn = aws_lb_listener.http[0].arn
  priority     = 110

  action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.minio_console[0].arn
  }

  condition {
    path_pattern {
      values = ["/minio-console", "/minio-console/*"]
    }
  }
}
