data "aws_ssm_parameter" "rabbitmq_user" {
  provider = aws.paris
  name     = "/codabench-loadtest/rabbitmq-user"
}

data "aws_ssm_parameter" "rabbitmq_password" {
  provider        = aws.paris
  name            = "/codabench-loadtest/rabbitmq-password"
  with_decryption = true
}

data "aws_ssm_parameter" "codabench_username" {
  provider = aws.paris
  name     = "/codabench-loadtest/codabench-username"
}

data "aws_ssm_parameter" "codabench_password" {
  provider        = aws.paris
  name            = "/codabench-loadtest/codabench-password"
  with_decryption = true
}
