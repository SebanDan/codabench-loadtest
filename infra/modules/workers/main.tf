resource "aws_launch_template" "this" {
  name_prefix   = "${var.name_prefix}-lt-"
  image_id      = var.ami_id
  instance_type = var.instance_type
  key_name      = var.key_name
  user_data     = base64encode(var.user_data)

  vpc_security_group_ids = var.security_group_ids

  dynamic "iam_instance_profile" {
    for_each = var.iam_instance_profile_name == null ? [] : [var.iam_instance_profile_name]

    content {
      name = iam_instance_profile.value
    }
  }

  block_device_mappings {
    device_name = "/dev/xvda"

    ebs {
      volume_size = var.root_volume_size
      volume_type = "gp3"
      encrypted   = true
    }
  }

  tag_specifications {
    resource_type = "instance"

    tags = merge(var.tags, {
      Name = "${var.name_prefix}-worker"
      Role = "worker"
    })
  }

  update_default_version = true
}

resource "aws_autoscaling_group" "this" {
  name                = "${var.name_prefix}-asg"
  min_size            = var.min_size
  max_size            = var.max_size
  desired_capacity    = var.desired_capacity
  vpc_zone_identifier = var.subnet_ids
  health_check_type   = "EC2"

  launch_template {
    id      = aws_launch_template.this.id
    version = "$Latest"
  }

  dynamic "tag" {
    for_each = merge(var.tags, {
      Name = "${var.name_prefix}-worker"
      Role = "worker"
    })

    content {
      key                 = tag.key
      value               = tag.value
      propagate_at_launch = true
    }
  }
}
