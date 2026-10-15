# Terraform: VPC + EKS on AWS

What `terraform apply` builds in `ap-south-1` (Mumbai):

```text
VPC 10.42.0.0/16
├── public subnets   10.42.128.0/20, 10.42.144.0/20   (one per AZ, tagged for internet-facing load balancers)
├── private subnets  10.42.0.0/20,   10.42.16.0/20    (worker nodes live here)
├── internet gateway + 1 NAT gateway (shared, to keep cost down)
└── EKS cluster "shelfwise-eks" (Kubernetes 1.34)
    ├── add-ons: vpc-cni, coredns, kube-proxy, pod-identity-agent, metrics-server
    └── managed node group "general": 2 × t3.medium (min 1, max 3)
```

It uses the community modules `terraform-aws-modules/vpc` (6.x) and `terraform-aws-modules/eks` (21.x), pinned in `.terraform.lock.hcl`.

## Without an AWS account

These run fully offline, and CI runs them on every push:

```bash
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
terraform test          # mocked AWS provider, see tests/infrastructure.tftest.hcl
```

`terraform test` simulates a plan and an apply of the whole stack against a mock provider and checks:
2 AZs, the subnet CIDRs, exactly one NAT gateway, the node group, and that bad input (1 AZ, an unknown capacity type) is rejected.

`terraform plan` and `apply` do need real credentials, because the provider has to ask AWS what already exists.

## With an AWS account

```bash
aws configure                      # or: export AWS_PROFILE=...
aws sts get-caller-identity        # make sure you're in the right account
cp terraform.tfvars.example terraform.tfvars

terraform init
terraform plan -out tfplan         # screenshot this
terraform apply tfplan             # ~15 minutes, EKS is slow to create
$(terraform output -raw configure_kubectl)
kubectl get nodes
```

Then deploy with the Helm chart, using `helm/shelfwise/values-eks.yaml`. See the root README.

**Destroy as soon as you've taken your screenshots:**

```bash
helm uninstall shelfwise -n shelfwise   # removes the Service/Ingress load balancers first
terraform destroy
```

If `destroy` hangs on the VPC, a load balancer created by Kubernetes is still attached. Uninstall the Helm release (or delete it in the EC2 → Load Balancers console), then run `destroy` again.

### Rough cost (ap-south-1, on-demand)

| Item | Per hour |
|---|---|
| EKS control plane | $0.10 |
| 2 × t3.medium nodes | ~$0.09 |
| NAT gateway (+ data) | ~$0.06 |
| **Total** | **≈ $0.25/h**, so a 2-hour demo costs about $0.50 |

`node_capacity_type = "SPOT"` cuts the node cost by roughly two-thirds.
