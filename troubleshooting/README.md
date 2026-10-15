# Troubleshooting labs

Four failures you can break and fix live. Each one starts from a healthy `shelfwise` namespace.

## 1. ImagePullBackOff: the image tag doesn't exist

```bash
kubectl apply -f troubleshooting/broken-image.yaml
kubectl get pods -n shelfwise -l lab=broken-image          # ErrImagePull -> ImagePullBackOff
kubectl describe pod -n shelfwise -l lab=broken-image      # Events: "Failed to pull image ...v9.9.9-does-not-exist"
kubectl get events -n shelfwise --sort-by=.lastTimestamp | tail
```

**Cause:** the tag was never pushed. CI only ever pushes commit SHAs. The registry answers `not found` for a public package; for a private or missing package GHCR answers `403 Forbidden` instead, which is also what a missing `imagePullSecret` looks like.
**Fix:** point it at a tag that exists, or delete it:

```bash
kubectl delete -f troubleshooting/broken-image.yaml
```

## 2. Service with no endpoints: label mismatch

```bash
kubectl apply -f troubleshooting/broken-service.yaml
kubectl get endpointslices -n shelfwise -l kubernetes.io/service-name=shelfwise-api-broken   # no endpoints
kubectl get pods -n shelfwise --show-labels | grep backend                                  # component=backend
kubectl get svc shelfwise-api-broken -n shelfwise -o jsonpath='{.spec.selector}'; echo      # component=api
```

**Cause:** a Service finds its pods only by label selector. `component=api` matches nothing, so there are no endpoints and every request times out.
**Fix:**

```bash
kubectl patch svc shelfwise-api-broken -n shelfwise --type merge \
  -p '{"spec":{"selector":{"app.kubernetes.io/name":"shelfwise","app.kubernetes.io/component":"backend"}}}'
kubectl get endpointslices -n shelfwise -l kubernetes.io/service-name=shelfwise-api-broken   # 2 endpoints now
kubectl delete -f troubleshooting/broken-service.yaml
```

## 3. Running but not Ready: the database password is wrong

```bash
kubectl set env deploy/shelfwise-backend -n shelfwise \
  DATABASE_URL='postgresql+psycopg://shelfwise:wrong@shelfwise-postgres:5432/shelfwise'
kubectl get pods -n shelfwise -w            # new pod sits at 0/1 or restarts: alembic can't log in
kubectl logs -n shelfwise deploy/shelfwise-backend --tail=20   # "password authentication failed"
```

Because of `maxUnavailable: 0`, the old pods keep serving and users notice nothing. The readiness gate protects the rollout.

**Fix:** roll back to the previous ReplicaSet:

```bash
kubectl rollout undo deploy/shelfwise-backend -n shelfwise
kubectl rollout status deploy/shelfwise-backend -n shelfwise
```

## 4. Forbidden: Pod Security Admission

```bash
kubectl run root-shell -n shelfwise --image=nginx
# Error from server (Forbidden): ... violates PodSecurity "restricted:latest": allowPrivilegeEscalation != false ...
```

**Cause:** `k8s/namespace.yaml` enforces the *restricted* Pod Security Standard, so pods running as root or keeping Linux capabilities are rejected at admission. Every Shelfwise pod (and `scripts/load-test.sh`) sets `runAsNonRoot`, drops all capabilities and uses a RuntimeDefault seccomp profile.
