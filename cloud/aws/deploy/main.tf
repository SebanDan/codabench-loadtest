module "paris" {
  source = "./modules/paris"

  providers = {
    aws = aws.paris
  }

  name_prefix                 = var.name_prefix
  codabench_vpc_name          = var.codabench_vpc_name
  codabench_private_rt_name   = var.codabench_private_rt_name
  codabench_alb_name          = var.codabench_alb_name
  codabench_alb_sg_name       = var.codabench_alb_sg_name
  codabench_app_sg_name       = var.codabench_app_sg_name
  locust_subnet_cidr          = var.paris_locust_subnet_cidr
  locust_subnet_az            = var.paris_locust_subnet_az
  master_instance_type        = var.master_instance_type
  worker_instance_type        = var.worker_instance_type
  playwright_instance_type    = var.playwright_instance_type
  worker_min_size             = var.paris_worker_min
  worker_max_size             = var.paris_worker_max
  worker_desired_capacity     = var.paris_worker_desired
  iam_instance_profile_name   = aws_iam_instance_profile.locust_paris.name
  repo_url                    = var.loadtest_repo_url
  repo_branch                 = var.loadtest_repo_branch
  results_bucket              = aws_s3_bucket.results.bucket
  codabench_app_ip            = var.codabench_app_ip
  codabench_rabbitmq_user     = data.aws_ssm_parameter.rabbitmq_user.value
  codabench_rabbitmq_password = data.aws_ssm_parameter.rabbitmq_password.value
  codabench_username          = data.aws_ssm_parameter.codabench_username.value
  codabench_password          = data.aws_ssm_parameter.codabench_password.value
}

module "us_east" {
  source = "./modules/remote_region"

  providers = {
    aws = aws.us_east
  }

  name_prefix               = var.name_prefix
  region_name               = "us-east"
  vpc_cidr                  = var.us_east_vpc_cidr
  worker_instance_type      = var.worker_instance_type
  worker_min_size           = var.us_east_worker_min
  worker_max_size           = var.us_east_worker_max
  worker_desired_capacity   = var.us_east_worker_desired
  iam_instance_profile_name = aws_iam_instance_profile.locust_us_east.name
  alb_dns                   = module.paris.alb_dns
  repo_url                  = var.loadtest_repo_url
  repo_branch               = var.loadtest_repo_branch
  results_bucket            = aws_s3_bucket.results.bucket
  codabench_username        = data.aws_ssm_parameter.codabench_username.value
  codabench_password        = data.aws_ssm_parameter.codabench_password.value
}

module "ap_southeast" {
  source = "./modules/remote_region"

  providers = {
    aws = aws.ap_southeast
  }

  name_prefix               = var.name_prefix
  region_name               = "ap-southeast"
  vpc_cidr                  = var.ap_southeast_vpc_cidr
  worker_instance_type      = var.worker_instance_type
  worker_min_size           = var.ap_southeast_worker_min
  worker_max_size           = var.ap_southeast_worker_max
  worker_desired_capacity   = var.ap_southeast_worker_desired
  iam_instance_profile_name = aws_iam_instance_profile.locust_ap_southeast.name
  alb_dns                   = module.paris.alb_dns
  repo_url                  = var.loadtest_repo_url
  repo_branch               = var.loadtest_repo_branch
  results_bucket            = aws_s3_bucket.results.bucket
  codabench_username        = data.aws_ssm_parameter.codabench_username.value
  codabench_password        = data.aws_ssm_parameter.codabench_password.value
}
