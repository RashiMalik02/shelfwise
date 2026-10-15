variable "aws_region" {
  description = "Region to build everything in. ap-south-1 is Mumbai."
  type        = string
  default     = "ap-south-1"
}

variable "project" {
  description = "Used as a prefix for resource names and as a cost-allocation tag."
  type        = string
  default     = "shelfwise"
}

variable "environment" {
  description = "Environment label (dev, staging, prod)."
  type        = string
  default     = "dev"
}

variable "owner" {
  description = "Who to ask before deleting these resources."
  type        = string
  default     = "rashimalik02"
}

variable "cluster_name" {
  description = "EKS cluster name. The deploy-eks CI job uses the same default."
  type        = string
  default     = "shelfwise-eks"
}

variable "kubernetes_version" {
  description = "EKS control-plane version."
  type        = string
  default     = "1.34"
}

variable "vpc_cidr" {
  description = "Address range for the whole VPC."
  type        = string
  default     = "10.42.0.0/16"

  validation {
    condition     = can(cidrhost(var.vpc_cidr, 0)) && tonumber(split("/", var.vpc_cidr)[1]) <= 20
    error_message = "vpc_cidr must be a valid CIDR block of /20 or larger."
  }
}

variable "az_count" {
  description = "How many availability zones to spread subnets across (one public + one private subnet per AZ)."
  type        = number
  default     = 2

  validation {
    condition     = var.az_count >= 2 && var.az_count <= 3
    error_message = "EKS needs subnets in at least two AZs; this project supports 2 or 3."
  }
}

variable "single_nat_gateway" {
  description = "One shared NAT gateway instead of one per AZ. Much cheaper, fine for a demo, not highly available."
  type        = bool
  default     = true
}

variable "node_instance_types" {
  description = "EC2 instance types for the managed node group."
  type        = list(string)
  default     = ["t3.medium"]
}

variable "node_capacity_type" {
  description = "ON_DEMAND or SPOT. SPOT is ~60-70% cheaper but nodes can be reclaimed."
  type        = string
  default     = "ON_DEMAND"

  validation {
    condition     = contains(["ON_DEMAND", "SPOT"], var.node_capacity_type)
    error_message = "node_capacity_type must be ON_DEMAND or SPOT."
  }
}

variable "node_min_size" {
  type    = number
  default = 1
}

variable "node_desired_size" {
  type    = number
  default = 2
}

variable "node_max_size" {
  type    = number
  default = 3
}

variable "cluster_endpoint_public_access_cidrs" {
  description = "Who may reach the Kubernetes API. Tighten this to your own IP (x.x.x.x/32) when you can."
  type        = list(string)
  default     = ["0.0.0.0/0"]
}
