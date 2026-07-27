data "aws_vpc" "codabench" {
  filter {
    name   = "tag:Name"
    values = [var.codabench_vpc_name]
  }
}

data "aws_route_table" "private" {
  filter {
    name   = "tag:Name"
    values = [var.codabench_private_rt_name]
  }
}

data "aws_security_group" "alb" {
  filter {
    name   = "tag:Name"
    values = [var.codabench_alb_sg_name]
  }
  vpc_id = data.aws_vpc.codabench.id
}

data "aws_security_group" "codabench" {
  filter {
    name   = "tag:Name"
    values = [var.codabench_app_sg_name]
  }
  vpc_id = data.aws_vpc.codabench.id
}

data "aws_lb" "codabench" {
  name = var.codabench_alb_name
}

data "aws_ami" "al2023" {
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
}
