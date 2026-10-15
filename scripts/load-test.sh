#!/usr/bin/env bash
# Generates enough API traffic from inside the cluster to push backend CPU over
# the HPA target, so you can watch it scale:
#   terminal 1:  kubectl get hpa -n shelfwise -w
#   terminal 2:  scripts/load-test.sh 180      (seconds, default 120)
set -euo pipefail

DURATION="${1:-120}"
WORKERS="${WORKERS:-12}"
NAMESPACE=shelfwise
TARGET="http://shelfwise-backend:8000"

kubectl -n "$NAMESPACE" delete pod loadgen --ignore-not-found >/dev/null

# The namespace enforces the "restricted" Pod Security Standard, so even the
# load generator has to run as non-root with all capabilities dropped.
kubectl -n "$NAMESPACE" run loadgen --image=busybox:1.37 --restart=Never --overrides='{
  "spec": {
    "securityContext": {"runAsNonRoot": true, "runAsUser": 65534, "seccompProfile": {"type": "RuntimeDefault"}},
    "containers": [{
      "name": "loadgen",
      "image": "busybox:1.37",
      "command": ["sh", "-c", "end=$(( $(date +%s) + '"$DURATION"' )); for w in $(seq '"$WORKERS"'); do (while [ $(date +%s) -lt $end ]; do wget -q -O /dev/null '"$TARGET"'/api/products; wget -q -O /dev/null '"$TARGET"'/api/stats; wget -q -O /dev/null \"'"$TARGET"'/api/products?q=box\"; done) & done; wait; echo done"],
      "securityContext": {"allowPrivilegeEscalation": false, "capabilities": {"drop": ["ALL"]}},
      "resources": {"requests": {"cpu": "50m", "memory": "16Mi"}, "limits": {"cpu": "500m", "memory": "64Mi"}}
    }]
  }
}'

echo "load generator running for ${DURATION}s with ${WORKERS} workers against ${TARGET}"
echo "watch:  kubectl get hpa -n ${NAMESPACE} -w"
