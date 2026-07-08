terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_instance" "this" {
  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = var.subnet_id
  vpc_security_group_ids      = var.security_group_ids
  key_name                    = var.key_name
  iam_instance_profile        = var.iam_instance_profile_name
  associate_public_ip_address = var.associate_public_ip
  private_ip                  = var.private_ip
  user_data                   = var.user_data
  source_dest_check           = var.source_dest_check

  root_block_device {
    volume_size = var.root_volume_size
    volume_type = var.root_volume_type
    encrypted   = true
  }

  dynamic "ebs_block_device" {
    for_each = var.additional_ebs_block_devices
    content {
      device_name = ebs_block_device.value.device_name
      volume_size = ebs_block_device.value.volume_size
      volume_type = ebs_block_device.value.volume_type
      encrypted   = ebs_block_device.value.encrypted
    }
  }

  tags = merge(var.tags, {
    Name = var.name
  })

  lifecycle {
    ignore_changes = [
      user_data,
    ]
  }
}
