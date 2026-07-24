resource "aws_launch_template" "locust_worker" {
  name_prefix   = "${var.name_prefix}-locust-worker-"
  image_id      = data.aws_ami.al2023.id
  instance_type = var.worker_instance_type

  vpc_security_group_ids = [aws_security_group.locust.id]

  iam_instance_profile {
    name = var.iam_instance_profile_name
  }

  user_data = base64encode(templatefile("${path.module}/../../templates/locust_worker_paris.sh.tftpl", {
    repo_url       = var.repo_url
    repo_branch    = var.repo_branch
    results_bucket = var.results_bucket
    region_name    = "paris"
    master_ip      = aws_instance.locust_master.private_ip
    alb_dns        = data.aws_lb.codabench.dns_name
  }))

  block_device_mappings {
    device_name = "/dev/xvda"
    ebs {
      volume_size = 30
      volume_type = "gp3"
      encrypted   = true
    }
  }

  tag_specifications {
    resource_type = "instance"
    tags = {
      Name      = "${var.name_prefix}-locust-worker"
      Role      = "locust-worker"
      Project   = var.name_prefix
      ManagedBy = "terraform"
    }
  }

  update_default_version = true
}

resource "aws_autoscaling_group" "locust_workers" {
  name                = "${var.name_prefix}-locust-workers-asg"
  min_size            = var.worker_min_size
  max_size            = var.worker_max_size
  desired_capacity    = var.worker_desired_capacity
  vpc_zone_identifier = [aws_subnet.locust.id]
  health_check_type   = "EC2"

  launch_template {
    id      = aws_launch_template.locust_worker.id
    version = "$Latest"
  }

  tag {
    key                 = "Name"
    value               = "${var.name_prefix}-locust-worker"
    propagate_at_launch = true
  }

  tag {
    key                 = "Project"
    value               = var.name_prefix
    propagate_at_launch = true
  }
}
