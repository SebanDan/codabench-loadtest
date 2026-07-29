# NLB to expose Locust master ports (5557-5558) to remote workers.
# Remote workers in US/Asia connect to the NLB DNS to join the master.

resource "aws_lb" "locust_master" {
  name               = "${var.name_prefix}-master-nlb"
  internal           = false
  load_balancer_type = "network"
  subnets            = data.aws_subnets.public.ids

  tags = {
    Name      = "${var.name_prefix}-master-nlb"
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }
}

data "aws_subnets" "public" {
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.codabench.id]
  }

  filter {
    name   = "map-public-ip-on-launch"
    values = ["true"]
  }
}

resource "aws_lb_target_group" "locust_master_5557" {
  name        = "${var.name_prefix}-master-5557"
  port        = 5557
  protocol    = "TCP"
  vpc_id      = data.aws_vpc.codabench.id
  target_type = "instance"

  health_check {
    protocol = "TCP"
    port     = 5557
  }

  tags = {
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }
}

resource "aws_lb_target_group" "locust_master_5558" {
  name        = "${var.name_prefix}-master-5558"
  port        = 5558
  protocol    = "TCP"
  vpc_id      = data.aws_vpc.codabench.id
  target_type = "instance"

  health_check {
    protocol = "TCP"
    port     = 5558
  }

  tags = {
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }
}

resource "aws_lb_target_group_attachment" "master_5557" {
  target_group_arn = aws_lb_target_group.locust_master_5557.arn
  target_id        = aws_instance.locust_master.id
  port             = 5557
}

resource "aws_lb_target_group_attachment" "master_5558" {
  target_group_arn = aws_lb_target_group.locust_master_5558.arn
  target_id        = aws_instance.locust_master.id
  port             = 5558
}

resource "aws_lb_listener" "locust_5557" {
  load_balancer_arn = aws_lb.locust_master.arn
  port              = 5557
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.locust_master_5557.arn
  }
}

resource "aws_lb_listener" "locust_5558" {
  load_balancer_arn = aws_lb.locust_master.arn
  port              = 5558
  protocol          = "TCP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.locust_master_5558.arn
  }
}
