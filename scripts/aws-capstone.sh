#!/usr/bin/env bash
# One sitting on AWS for the Terraform module of the capstone, built to spend as little as possible:
#   preflight -> plan (saved to docs/aws/) -> apply -> kubectl check -> you take console
#   screenshots -> destroy. Expect ~30-40 min and well under $1 with the defaults below.
#
#   AWS_PROFILE=shelfwise ./scripts/aws-capstone.sh
set -euo pipefail
cd "$(dirname "$0")/../terraform"

export AWS_PROFILE="${AWS_PROFILE:-shelfwise}"
# Accounts made with AWS's new sign-up flow are locked to ONE region picked from the
# contact-address country (India -> ap-southeast-2, Sydney); every other region is denied by
# an AWS-managed SCP. Check yours at https://settings.aws.com -> Project -> Additional info.
REGION="${AWS_REGION:-ap-southeast-2}"
OUT=../docs/aws
mkdir -p "$OUT"

# Free-plan accounts may not request Spot capacity, so nodes are on-demand; one NAT gateway instead of two.
TF_VARS=(-var "aws_region=$REGION" -var "node_capacity_type=${CAPACITY:-ON_DEMAND}" -var "node_desired_size=2" -var "single_nat_gateway=true")

echo "==> preflight"
aws sts get-caller-identity --query Arn --output text
if ! aws ec2 describe-vpcs --region "$REGION" --max-items 1 >/dev/null 2>&1; then
  echo "ec2:DescribeVpcs is denied. If the error mentions a service control policy, the account's"
  echo "AWS Organization blocks EC2/EKS and nothing here can work until that is lifted."
  aws ec2 describe-vpcs --region "$REGION" --max-items 1 || true
  exit 1
fi
aws eks list-clusters --region "$REGION" >/dev/null

trap 'echo; echo "!! Script stopped. If anything was created, run: cd terraform && terraform destroy ${TF_VARS[*]}"' ERR

echo "==> terraform init + plan"
terraform init -input=false
terraform plan -input=false "${TF_VARS[@]}" -out tfplan | tee "$OUT/terraform-plan.txt"

read -r -p "Apply this plan? EKS + NAT + 2 t3.medium nodes cost about \$0.27/hour until destroyed. [y/N] " ok
[ "$ok" = "y" ] || { echo "Not applied."; exit 0; }

START=$(date +%s)
terraform apply -input=false tfplan | tee "$OUT/terraform-apply.txt"
terraform output | tee "$OUT/terraform-output.txt"

echo "==> kubectl"
aws eks update-kubeconfig --region "$REGION" --name "$(terraform output -raw cluster_name)" --alias shelfwise-eks
kubectl get nodes -o wide | tee "$OUT/kubectl-get-nodes.txt"

cat <<EOF

Take your screenshots now (AWS Console, region $REGION):
  - VPC  -> Your VPCs: shelfwise-dev-vpc, and Subnets (2 public + 2 private)
  - EKS  -> Clusters -> shelfwise-eks -> Compute tab (node group "general")
Saved terminal output is in docs/aws/.
EOF
read -r -p "Press Enter when done to DESTROY everything... " _

echo "==> terraform destroy"
terraform destroy -input=false -auto-approve "${TF_VARS[@]}" | tee "$OUT/terraform-destroy.txt"
kubectl config delete-context shelfwise-eks >/dev/null 2>&1 || true
trap - ERR

MINUTES=$(( ($(date +%s) - START) / 60 ))
echo
echo "Done. Resources existed for about ${MINUTES} minutes."
echo "Double-check in the console that EC2 -> NAT gateways, Load balancers and EKS clusters are empty."
