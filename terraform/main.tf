data "aws_availability_zones" "available" {
  state = "available"

  # Skip Local Zones / Wavelength zones, EKS can't place control-plane ENIs there.
  filter {
    name   = "opt-in-status"
    values = ["opt-in-not-required"]
  }
}

locals {
  name = "${var.project}-${var.environment}"
  azs  = slice(data.aws_availability_zones.available.names, 0, var.az_count)

  # /16 split into /20s: the first block(s) for private subnets, a later range for public ones.
  private_subnets = [for i in range(var.az_count) : cidrsubnet(var.vpc_cidr, 4, i)]
  public_subnets  = [for i in range(var.az_count) : cidrsubnet(var.vpc_cidr, 4, i + 8)]

  tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
  }
}

# ------------------------------------------------------------------ network
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 6.0"

  name = "${local.name}-vpc"
  cidr = var.vpc_cidr
  azs  = local.azs

  public_subnets  = local.public_subnets
  private_subnets = local.private_subnets

  # Worker nodes live in private subnets and reach the internet (GHCR, Docker Hub) through NAT.
  enable_nat_gateway   = true
  single_nat_gateway   = var.single_nat_gateway
  enable_dns_hostnames = true
  enable_dns_support   = true

  # These tags tell the AWS Load Balancer Controller where internet-facing and
  # internal load balancers may be created.
  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = 1
  }
}

# ------------------------------------------------------------------ EKS
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name               = var.cluster_name
  kubernetes_version = var.kubernetes_version

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets

  endpoint_public_access       = true
  endpoint_public_access_cidrs = var.cluster_endpoint_public_access_cidrs

  # Whoever runs `terraform apply` gets cluster-admin, so kubectl works straight away.
  enable_cluster_creator_admin_permissions = true

  addons = {
    coredns    = {}
    kube-proxy = {}
    vpc-cni = {
      before_compute = true
    }
    eks-pod-identity-agent = {
      before_compute = true
    }
    # Needed by the HorizontalPodAutoscaler to read pod CPU usage.
    metrics-server = {}
  }

  eks_managed_node_groups = {
    general = {
      instance_types = var.node_instance_types
      capacity_type  = var.node_capacity_type
      ami_type       = "AL2023_x86_64_STANDARD"

      min_size     = var.node_min_size
      desired_size = var.node_desired_size
      max_size     = var.node_max_size

      labels = {
        workload = "general"
      }
    }
  }
}
