resource "aws_subnet" "locust" {
  vpc_id                  = data.aws_vpc.codabench.id
  cidr_block              = var.locust_subnet_cidr
  availability_zone       = var.locust_subnet_az
  map_public_ip_on_launch = false

  tags = {
    Name      = "${var.name_prefix}-locust-subnet"
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }
}

resource "aws_route_table_association" "locust" {
  subnet_id      = aws_subnet.locust.id
  route_table_id = data.aws_route_table.private.id
}
