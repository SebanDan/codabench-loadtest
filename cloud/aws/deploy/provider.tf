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
    key    = "locust-loadtest/terraform.tfstate"
    region = "eu-west-1"
  }
}

provider "aws" {
  alias   = "paris"
  region  = "eu-west-1"
  profile = var.aws_profile
}

provider "aws" {
  alias   = "us_east"
  region  = "us-east-1"
  profile = var.aws_profile
}

provider "aws" {
  alias   = "ap_southeast"
  region  = "ap-southeast-1"
  profile = var.aws_profile
}
