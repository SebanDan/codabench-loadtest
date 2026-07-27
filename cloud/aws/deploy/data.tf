data "aws_ssm_parameter" "rabbitmq_user" {
  provider = aws.paris
  name     = "/codabench-loadtest/rabbitmq-user"
}

data "aws_ssm_parameter" "rabbitmq_password" {
  provider        = aws.paris
  name            = "/codabench-loadtest/rabbitmq-password"
  with_decryption = true
}
