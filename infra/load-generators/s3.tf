resource "aws_s3_bucket" "results" {
  provider = aws.paris
  bucket   = var.results_bucket_name

  tags = {
    Name      = var.results_bucket_name
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }
}

resource "aws_s3_bucket_versioning" "results" {
  provider = aws.paris
  bucket   = aws_s3_bucket.results.id

  versioning_configuration {
    status = "Enabled"
  }
}
