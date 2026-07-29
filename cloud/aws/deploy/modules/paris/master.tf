resource "aws_instance" "locust_master" {
  ami                         = data.aws_ami.al2023.id
  instance_type               = var.master_instance_type
  subnet_id                   = aws_subnet.locust.id
  vpc_security_group_ids      = [aws_security_group.locust.id]
  iam_instance_profile        = var.iam_instance_profile_name
  associate_public_ip_address = false

  user_data = templatefile("${path.module}/../../templates/locust_master.sh.tftpl", {
    repo_url           = var.repo_url
    repo_branch        = var.repo_branch
    results_bucket     = var.results_bucket
    region_name        = "paris"
    codabench_app_ip   = var.codabench_app_ip
    rabbitmq_user      = var.codabench_rabbitmq_user
    rabbitmq_password  = var.codabench_rabbitmq_password
    codabench_username = var.codabench_username
    codabench_password = var.codabench_password
    alb_dns            = data.aws_lb.codabench.dns_name
  })

  root_block_device {
    volume_size = 30
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name      = "${var.name_prefix}-locust-master"
    Role      = "locust-master"
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }

  lifecycle {
    ignore_changes = [user_data]
  }
}
