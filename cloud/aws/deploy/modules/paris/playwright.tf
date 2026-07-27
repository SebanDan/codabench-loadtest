resource "aws_instance" "playwright" {
  ami                         = data.aws_ami.al2023.id
  instance_type               = var.playwright_instance_type
  subnet_id                   = aws_subnet.locust.id
  vpc_security_group_ids      = [aws_security_group.locust.id]
  iam_instance_profile        = var.iam_instance_profile_name
  associate_public_ip_address = false

  user_data = templatefile("${path.module}/../../templates/playwright.sh.tftpl", {
    repo_url       = var.repo_url
    repo_branch    = var.repo_branch
    results_bucket = var.results_bucket
    region_name    = "paris"
    alb_dns        = data.aws_lb.codabench.dns_name
  })

  root_block_device {
    volume_size = 50
    volume_type = "gp3"
    encrypted   = true
  }

  tags = {
    Name      = "${var.name_prefix}-playwright"
    Role      = "playwright"
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }

  lifecycle {
    ignore_changes = [user_data]
  }
}
