# `terraform test` runs these against a mocked AWS provider: no account, no
# credentials and no cost. It exercises the module wiring, CIDR maths and
# variable validation. Real resources still need `terraform apply`.

mock_provider "aws" {
  mock_data "aws_availability_zones" {
    defaults = {
      names    = ["ap-south-1a", "ap-south-1b", "ap-south-1c"]
      zone_ids = ["aps1-az1", "aps1-az3", "aps1-az2"]
    }
  }

  mock_data "aws_caller_identity" {
    defaults = {
      account_id = "123456789012"
      arn        = "arn:aws:iam::123456789012:user/ci"
    }
  }

  mock_data "aws_partition" {
    defaults = {
      partition  = "aws"
      dns_suffix = "amazonaws.com"
    }
  }

  mock_data "aws_iam_session_context" {
    defaults = {
      issuer_arn = "arn:aws:iam::123456789012:user/ci"
    }
  }

  mock_data "aws_iam_policy_document" {
    defaults = {
      json = "{\"Version\":\"2012-10-17\",\"Statement\":[]}"
    }
  }

  mock_resource "aws_iam_role" {
    defaults = {
      arn = "arn:aws:iam::123456789012:role/mock"
    }
  }

  mock_resource "aws_iam_policy" {
    defaults = {
      arn = "arn:aws:iam::123456789012:policy/mock"
    }
  }

  mock_resource "aws_eks_cluster" {
    defaults = {
      arn      = "arn:aws:eks:ap-south-1:123456789012:cluster/shelfwise-eks"
      endpoint = "https://mock.gr7.ap-south-1.eks.amazonaws.com"
      certificate_authority = [{
        data = "bW9jaw=="
      }]
      identity = [{
        oidc = [{
          issuer = "https://oidc.eks.ap-south-1.amazonaws.com/id/MOCK"
        }]
      }]
    }
  }

  mock_data "aws_eks_addon_version" {
    defaults = {
      version = "v1.20.0-eksbuild.1"
    }
  }

  mock_resource "aws_launch_template" {
    defaults = {
      id = "lt-0123456789abcdef0"
    }
  }
}

# The EKS module fetches the OIDC issuer's TLS certificate; mock that too.
mock_provider "tls" {
  mock_data "tls_certificate" {
    defaults = {
      certificates = [{
        sha1_fingerprint = "9e99a48a9960b14926bb7f3b02e22da2b0ab7280"
      }]
    }
  }
}

run "network_layout" {
  command = plan

  assert {
    condition     = length(local.azs) == 2
    error_message = "Expected subnets in exactly two availability zones by default."
  }

  assert {
    condition     = local.public_subnets == ["10.42.128.0/20", "10.42.144.0/20"]
    error_message = "Public subnets are not carved out of the VPC range as expected."
  }

  assert {
    condition     = local.private_subnets == ["10.42.0.0/20", "10.42.16.0/20"]
    error_message = "Private subnets are not carved out of the VPC range as expected."
  }

  assert {
    condition     = module.vpc.name == "shelfwise-dev-vpc"
    error_message = "VPC name should follow <project>-<environment>-vpc."
  }
}

run "full_stack_with_mocked_aws" {
  # A simulated apply: every resource is "created" by the mock provider.
  command = apply

  assert {
    condition     = length(module.vpc.public_subnets) == 2
    error_message = "Two public subnets should be created."
  }

  assert {
    condition     = length(module.vpc.private_subnets) == 2
    error_message = "Two private subnets should be created."
  }

  assert {
    condition     = length(module.vpc.natgw_ids) == 1
    error_message = "single_nat_gateway=true should create exactly one NAT gateway."
  }

  assert {
    condition     = module.eks.cluster_name == "shelfwise-eks"
    error_message = "Cluster name should come from var.cluster_name."
  }

  assert {
    condition     = contains(keys(module.eks.eks_managed_node_groups), "general")
    error_message = "The managed node group 'general' is missing."
  }

  assert {
    condition     = output.configure_kubectl == "aws eks update-kubeconfig --region ap-south-1 --name shelfwise-eks"
    error_message = "configure_kubectl output is wrong."
  }
}

run "rejects_single_az" {
  command = plan

  variables {
    az_count = 1
  }

  expect_failures = [var.az_count]
}

run "rejects_unknown_capacity_type" {
  command = plan

  variables {
    node_capacity_type = "RESERVED"
  }

  expect_failures = [var.node_capacity_type]
}
