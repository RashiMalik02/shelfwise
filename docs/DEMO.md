# Demo run-sheet (about 12 minutes)

Have open before starting: the app tab (http://shelfwise.localtest.me), GitHub Actions, Grafana (port-forward on :3001), and two terminals.

## 0. Pre-flight (before the session)

```bash
./scripts/kind-up.sh            # skip if the cluster already exists
./scripts/argocd-up.sh          # GitOps: Argo CD now owns the shelfwise release
kubectl get pods -n shelfwise   # everything Running
kubectl -n monitoring port-forward svc/monitoring-grafana 3001:80 &
```

## 1. The app (2 min)

- Show the stock-health bar and the reorder queue. Click **Receive** on an item in the queue: it drops out of the queue and a new line appears in *Stock movements*.
- Try to pick more units than exist → the API returns 409 and the dialog won't submit.
- `/docs`: the same endpoints in Swagger.
- Point at the **build** pill in the header. It's the commit SHA of the running image. Note it down.

## 2. Change → pipeline (4 min)

Make a visible change, for example the page title in `frontend/src/components/Overview.jsx`:

```bash
git switch -c demo/title
# edit "Stockroom at a glance" -> "Stockroom today"
git commit -am "Rename overview heading to Stockroom today"
git push -u origin demo/title    # open a PR: tests + Trivy run, nothing is pushed
```

Merge the PR. On `main` the pipeline runs every stage: backend tests → frontend build → infra checks → build + Trivy + push (with the SHA tag) → *promote-gitops* commits the new tag.

## 3. Deployment updates (2 min)

```bash
kubectl get pods -n shelfwise -w    # new frontend/backend pods roll in, old ones terminate
```

Argo CD picks up the commit within a minute (or press *Refresh* in its UI). Reload the app: the heading has changed and the **build** pill shows the new SHA, the same one as in GHCR and in the Actions run.

## 4. Autoscaling + monitoring (3 min)

```bash
kubectl get hpa -n shelfwise -w          # terminal 1
./scripts/load-test.sh 180               # terminal 2
```

In Grafana ("Shelfwise · API & inventory"): requests/s climbs, then *Backend CPU per pod*, then *HPA replicas* steps from 2 up to 6. Prometheus → Status → Targets shows one UP target per pod.

## 5. Break it (1 min)

```bash
kubectl apply -f troubleshooting/broken-service.yaml
kubectl get endpointslices -n shelfwise -l kubernetes.io/service-name=shelfwise-api-broken   # empty
kubectl get pods -n shelfwise --show-labels | grep backend
```

Explain the selector mismatch, patch it, and the endpoints appear. Full labs: [`troubleshooting/README.md`](../troubleshooting/README.md).

## Questions people ask

- **Why tag with the SHA and not `latest`?** You can always trace a running pod back to the exact commit, and a rollback is just the previous SHA.
- **Why `/health` *and* `/ready`?** Liveness restarts a stuck process; readiness only takes the pod out of the Service. A DB outage should do the second, not the first.
- **Why Postgres in the cluster?** For the demo. On AWS I'd use RDS: backups, failover and patching come managed. The chart supports it via `postgres.externalDatabaseUrl`.
- **Why Traefik instead of ingress-nginx?** ingress-nginx was archived in March 2026. The Ingress object itself is the same; only `ingressClassName` changes.
