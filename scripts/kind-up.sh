#!/usr/bin/env bash
# Creates the local kind cluster and installs the platform pieces Shelfwise relies on:
# Traefik (ingress), metrics-server (HPA) and kube-prometheus-stack (Prometheus + Grafana).
set -euo pipefail
cd "$(dirname "$0")/.."

CLUSTER=shelfwise

if ! kind get clusters | grep -qx "$CLUSTER"; then
  kind create cluster --config k8s/kind-config.yaml
fi
kubectl config use-context "kind-$CLUSTER" >/dev/null

helm repo add traefik https://traefik.github.io/charts >/dev/null
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/ >/dev/null
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts >/dev/null
helm repo update >/dev/null

echo "==> namespace"
kubectl apply -f k8s/namespace.yaml

echo "==> traefik (ingress controller)"
helm upgrade --install traefik traefik/traefik --version 42.0.0 \
  -n traefik --create-namespace -f k8s/traefik-values.yaml --wait

echo "==> metrics-server"
helm upgrade --install metrics-server metrics-server/metrics-server --version 3.14.0 \
  -n kube-system -f monitoring/metrics-server-values.yaml --wait

echo "==> kube-prometheus-stack (this one takes a couple of minutes)"
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack --version 92.9.0 \
  -n monitoring --create-namespace -f monitoring/kube-prometheus-stack-values.yaml --wait --timeout 10m

kubectl get pods -A
echo
echo "Cluster ready. Next: scripts/deploy-local.sh"
