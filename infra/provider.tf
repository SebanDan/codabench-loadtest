terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  backend "s3" {
    bucket = "tf-codabench-backend"
    key    = "codabench-loadtest/terraform.tfstate"
    region = "eu-west-1"
  }
}

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile
}
