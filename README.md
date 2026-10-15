# Shelfwise

Shelfwise is an inventory manager for a small warehouse or stockroom. It tracks products (SKU, bin location, supplier, unit price), shows which items have dropped below their reorder point, and keeps a ledger of every stock movement: goods received, items picked/sold, returns, write-offs and stock counts.

It's my DevOps capstone. The application is deliberately small, so the focus is the path it takes from a laptop to a monitored Kubernetes cluster: tests, containers, a CI/CD pipeline with a security gate, infrastructure as code, Helm, autoscaling and observability.

![Shelfwise dashboard](docs/screenshots/m1-app-localhost-3000.png)

## What's in it

| Layer | Tech | Where |
|---|---|---|
| Frontend | React 19 + Vite, plain CSS, served by unprivileged nginx | [`frontend/`](frontend) |
| Backend | FastAPI, SQLAlchemy 2, Pydantic | [`backend/app/`](backend/app) |
| Database | PostgreSQL 17, schema managed by Alembic (2 migrations) | [`backend/alembic/`](backend/alembic) |
| Tests | pytest (29 tests, in-memory SQLite), ruff, node:test | [`backend/tests/`](backend/tests) |
| Containers | Multi-stage Dockerfiles, non-root, Compose for the full stack | [`docker-compose.yml`](docker-compose.yml) |
| CI/CD | GitHub Actions → Trivy → GHCR, images tagged with the commit SHA | [`.github/workflows/ci-cd.yml`](.github/workflows/ci-cd.yml) |
| Infrastructure | Terraform: VPC (2 public + 2 private subnets) and EKS | [`terraform/`](terraform) |
| Deployment | Helm chart: Ingress, HPA, PDBs, StatefulSet, ServiceMonitor | [`helm/shelfwise/`](helm/shelfwise) |
| GitOps | Argo CD watches the chart; CI bumps the image tag | [`gitops/`](gitops) |
| Monitoring | kube-prometheus-stack (Prometheus + Grafana), custom dashboard | [`monitoring/`](monitoring) |
| Labs | Four break-and-fix exercises | [`troubleshooting/`](troubleshooting) |

```text
 git push ──► GitHub Actions ───────────────────────────────────────────────────────────┐
              ├─ backend: ruff + pytest          ┐                                       │
              ├─ frontend: node:test + vite build├─ all must pass                        │
              ├─ helm lint + terraform validate/test┘                                    │
              ├─ docker build ─► Trivy (HIGH/CRITICAL = fail) ─► push ghcr.io/…:<sha>    │
              └─ deploy:  DEPLOY_TARGET=eks ─► helm upgrade on EKS                       │
                          otherwise        ─► commit new <sha> to values-release.yaml ───┘
                                                         │
                                                  Argo CD (kind) syncs
                                                         ▼
        ┌──────────────── Kubernetes namespace "shelfwise" (restricted PSS) ────────────────┐
        │  Ingress (Traefik)  /  ──► frontend Service ──► nginx pods ×2                     │
        │                     /api, /docs ──► backend Service ──► FastAPI pods ×2..6 (HPA)  │
        │                                                          │                        │
        │                                              postgres StatefulSet + PVC           │
        └───────────────────────────────────────────────────────────────────────────────────┘
              ▲ ServiceMonitor scrapes /metrics every 15s
        Prometheus ──► Grafana "Shelfwise · API & inventory" dashboard
```

## API

Interactive docs at `/docs`.

| Method | Path | What it does |
|---|---|---|
| GET | `/health` | Liveness. The process is up (never touches the DB) |
| GET | `/ready` | Readiness. Returns 503 until Postgres answers and the schema exists |
| GET | `/metrics` | Prometheus metrics: HTTP rate/latency plus inventory gauges |
| GET | `/api/products?q=&category=&status=OK\|LOW\|OUT` | List and filter products |
| GET | `/api/products/{id}` | One product |
| POST | `/api/products` | Create (opening stock is written to the ledger) |
| PUT | `/api/products/{id}` | Update; changing `quantity` is logged as a stock count |
| DELETE | `/api/products/{id}` | Delete the product and its movements |
| POST | `/api/products/{id}/adjust` | Record a movement (`RECEIVED`, `SOLD`, `RETURNED`, `DAMAGED`); 409 if it would go negative |
| GET | `/api/products/{id}/movements` | Ledger for one product |
| GET | `/api/movements` | Latest movements across all products |
| GET | `/api/stats` | Totals, inventory value, low/out counts, value by category |
| GET | `/api/categories` | Distinct categories |

Besides the standard `http_requests_total` / `http_request_duration_seconds`, the backend exports `shelfwise_stock_movements_total{reason}`, `shelfwise_units_on_hand` and `shelfwise_products_by_stock_status{status}`.

## Run it

### 1. Docker Compose (whole stack, one command)

```bash
docker compose up --build
```

- App: <http://localhost:3000>
- API docs: <http://localhost:8000/docs>
- Metrics: <http://localhost:8000/metrics>

The backend runs migrations on start and loads 14 demo products. `docker compose down -v` wipes the database.

### 2. Backend on its own

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -v                                 # uses in-memory SQLite, never your real DB

docker compose up -d postgres             # or any Postgres 14+
export DATABASE_URL=postgresql+psycopg://shelfwise:shelfwise@localhost:5432/shelfwise
alembic upgrade head && python -m app.seed
uvicorn app.main:app --reload             # http://localhost:8000/docs
```

Frontend dev server (proxies `/api` to :8000): `cd frontend && npm ci && npm run dev`.

### 3. Local Kubernetes (kind)

Needs Docker, [kind](https://kind.sigs.k8s.io), kubectl and Helm.

```bash
./scripts/kind-up.sh        # cluster + Traefik + metrics-server + Prometheus/Grafana
./scripts/deploy-local.sh   # build images, load into kind, helm upgrade --install
```

Open <http://shelfwise.localtest.me>. `*.localtest.me` resolves to 127.0.0.1, so you don't need to edit `/etc/hosts`.

```bash
kubectl get pods,svc,ingress,hpa -n shelfwise
helm list -n shelfwise

# Grafana (user admin)
kubectl -n monitoring get secret monitoring-grafana -o jsonpath='{.data.admin-password}' | base64 -d; echo
kubectl -n monitoring port-forward svc/monitoring-grafana 3001:80          # http://localhost:3001
kubectl -n monitoring port-forward svc/monitoring-prometheus 9090:9090     # http://localhost:9090/targets

# Autoscaling demo
kubectl get hpa -n shelfwise -w          # terminal 1
./scripts/load-test.sh 180               # terminal 2
```

### 4. AWS (EKS)

See [`terraform/README.md`](terraform/README.md). In short: `terraform apply` builds the VPC and EKS, `$(terraform output -raw configure_kubectl)` points kubectl at it, and the `deploy-eks` job in CI takes over once you set the repository variable `DEPLOY_TARGET=eks` and the `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` secrets. Run `terraform destroy` when you're done.

## CI/CD

Every push and pull request to `main` runs [`ci-cd.yml`](.github/workflows/ci-cd.yml):

1. **backend-tests**: `ruff check`, `ruff format --check`, `pytest -v --cov`. A failing test stops the pipeline here.
2. **frontend-build**: `npm ci`, `npm test`, `npm run build`.
3. **infra-lint**: `helm lint` with each values file, plus `terraform fmt`, `validate` and `test` (mocked AWS provider, no credentials).
4. **images** (backend and frontend in parallel): build → **Trivy** scan that fails on any fixable HIGH/CRITICAL → push `ghcr.io/rashimalik02/shelfwise-<service>:<full commit SHA>`. Pull requests build and scan but never push.
5. **deploy**: either `helm upgrade` on EKS, or a commit that writes the new SHA into `helm/shelfwise/values-release.yaml`, which Argo CD in the local cluster rolls out. The frontend header shows the SHA it was built from, so you can see the new version arrive in the browser.

Every third-party action is pinned to a full commit SHA rather than a tag. Tags can be moved: in March 2026 attackers force-pushed almost every `aquasecurity/trivy-action` tag to a commit that stole CI secrets (CVE-2026-33634). The pinned v0.36.0 was released after that incident.

## Security notes

- Both images run as non-root (backend uid 10001, nginx uid 101). In Kubernetes every container also has a read-only root filesystem, `allowPrivilegeEscalation: false` and all capabilities dropped, and the namespace enforces the **restricted** Pod Security Standard.
- The Postgres password is generated by the chart on first install and reused on upgrades. No credentials are committed; `terraform.tfvars` and `.env` are git-ignored.
- Trivy findings and how they were fixed: [`docs/TRIVY.md`](docs/TRIVY.md).

## Repository layout

```text
backend/            FastAPI app, Alembic migrations, pytest suite, Dockerfile
frontend/           React app, nginx config template, Dockerfile
docker-compose.yml  postgres + backend + frontend
.github/workflows/  CI/CD pipeline
terraform/          VPC + EKS, offline tests in terraform/tests
helm/shelfwise/     chart, values for local / EKS / GitOps, Grafana dashboard JSON
k8s/                namespace, kind cluster config, Traefik values
monitoring/         kube-prometheus-stack and metrics-server values
gitops/             Argo CD Application + install values
scripts/            kind-up, deploy-local, argocd-up, load-test
troubleshooting/    break-and-fix labs
docs/               submission checklist, Trivy notes, demo script, screenshots
```

Submission checklist with every screenshot: [`docs/SUBMISSION.md`](docs/SUBMISSION.md) · Presentation run-sheet: [`docs/DEMO.md`](docs/DEMO.md)
