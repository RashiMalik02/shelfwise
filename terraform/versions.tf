terraform {
  required_version = ">= 1.9.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }

  # State is local by default so the project works on a fresh AWS account.
  # For a shared setup, create the bucket once and uncomment:
  # backend "s3" {
  #   bucket       = "shelfwise-tfstate-<account-id>"
  #   key          = "eks/terraform.tfstate"
  #   region       = "ap-south-1"
  #   use_lockfile = true
  # }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = local.tags
  }
}
