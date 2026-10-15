#!/usr/bin/env bash
# Build both images from the current checkout, load them into kind, and helm-upgrade.
# The tag is the git commit SHA (plus -dirty for uncommitted changes), same idea as CI.
set -euo pipefail
cd "$(dirname "$0")/.."

CLUSTER=shelfwise
NAMESPACE=shelfwise
TAG="$(git rev-parse --short=12 HEAD)"
git diff --quiet HEAD -- backend frontend || TAG="${TAG}-dirty"

kubectl config use-context "kind-$CLUSTER" >/dev/null

echo "==> building images tagged $TAG"
docker build -t "shelfwise-backend:$TAG" backend
docker build -t "shelfwise-frontend:$TAG" --build-arg "APP_BUILD=$TAG" frontend

echo "==> loading images into kind"
kind load docker-image --name "$CLUSTER" "shelfwise-backend:$TAG" "shelfwise-frontend:$TAG"

echo "==> helm upgrade"
helm upgrade --install shelfwise helm/shelfwise \
  --namespace "$NAMESPACE" --create-namespace \
  -f helm/shelfwise/values-local.yaml \
  --set backend.image.repository=shelfwise-backend \
  --set backend.image.tag="$TAG" \
  --set frontend.image.repository=shelfwise-frontend \
  --set frontend.image.tag="$TAG" \
  --wait --timeout 5m

kubectl -n "$NAMESPACE" get pods,svc,ingress,hpa
echo
echo "Open http://shelfwise.localtest.me"
