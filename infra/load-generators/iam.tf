data "aws_iam_policy_document" "ec2_assume_role" {
  provider = aws.paris

  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "locust_role" {
  provider           = aws.paris
  name               = "${var.name_prefix}-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume_role.json

  tags = {
    Name      = "${var.name_prefix}-role"
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }
}

resource "aws_iam_role_policy_attachment" "locust_ssm" {
  provider   = aws.paris
  role       = aws_iam_role.locust_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "locust_s3_write" {
  provider = aws.paris
  name     = "${var.name_prefix}-s3-write"
  role     = aws_iam_role.locust_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "s3:PutObject",
        "s3:GetObject",
        "s3:ListBucket"
      ]
      Resource = [
        aws_s3_bucket.results.arn,
        "${aws_s3_bucket.results.arn}/*"
      ]
    }]
  })
}

resource "aws_iam_instance_profile" "locust_paris" {
  provider = aws.paris
  name     = "${var.name_prefix}-paris-profile"
  role     = aws_iam_role.locust_role.name

  tags = {
    Name      = "${var.name_prefix}-paris-profile"
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }
}

resource "aws_iam_instance_profile" "locust_us_east" {
  provider = aws.us_east
  name     = "${var.name_prefix}-us-east-profile"
  role     = aws_iam_role.locust_role.name

  tags = {
    Name      = "${var.name_prefix}-us-east-profile"
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }
}

resource "aws_iam_instance_profile" "locust_ap_southeast" {
  provider = aws.ap_southeast
  name     = "${var.name_prefix}-ap-southeast-profile"
  role     = aws_iam_role.locust_role.name

  tags = {
    Name      = "${var.name_prefix}-ap-southeast-profile"
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }
}
