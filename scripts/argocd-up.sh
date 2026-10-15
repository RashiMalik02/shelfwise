#!/usr/bin/env bash
# Installs Argo CD in the kind cluster and points it at this repo (GitOps delivery).
# Prerequisites: the repo is on GitHub and the two GHCR packages are public
# (GitHub -> Packages -> shelfwise-backend / shelfwise-frontend -> Package settings -> Change visibility).
set -euo pipefail
cd "$(dirname "$0")/.."

kubectl config use-context kind-shelfwise >/dev/null
helm repo add argo https://argoproj.github.io/argo-helm >/dev/null
helm repo update argo >/dev/null

helm upgrade --install argocd argo/argo-cd --version 10.10.5 \
  -n argocd --create-namespace -f gitops/argocd-values.yaml --wait --timeout 10m

# If shelfwise was installed by hand with deploy-local.sh, hand it over to Argo CD.
# The DB secret and the Postgres volume are kept, so data survives the switch.
if helm status shelfwise -n shelfwise >/dev/null 2>&1; then
  helm uninstall shelfwise -n shelfwise
fi

kubectl apply -f gitops/argocd-application.yaml

echo
echo "Argo CD UI:  kubectl -n argocd port-forward svc/argocd-server 8081:80  ->  http://localhost:8081"
echo "user: admin   password: $(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d)"
