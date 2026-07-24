data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  az          = data.aws_availability_zones.available.names[var.subnet_az_index]
  subnet_cidr = coalesce(var.subnet_cidr, cidrsubnet(var.vpc_cidr, 8, 1))
}

resource "aws_vpc" "this" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name      = "${var.name_prefix}-${var.region_name}-vpc"
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }
}

resource "aws_internet_gateway" "this" {
  vpc_id = aws_vpc.this.id

  tags = {
    Name      = "${var.name_prefix}-${var.region_name}-igw"
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.this.id
  cidr_block              = local.subnet_cidr
  availability_zone       = local.az
  map_public_ip_on_launch = true

  tags = {
    Name      = "${var.name_prefix}-${var.region_name}-public"
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.this.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.this.id
  }

  tags = {
    Name      = "${var.name_prefix}-${var.region_name}-public-rt"
    Project   = var.name_prefix
    ManagedBy = "terraform"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}
