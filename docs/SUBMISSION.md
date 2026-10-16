# Capstone submission checklist

Every rubric line with the file or screenshot that proves it. **Still to do** marks the items that only exist after the repo is pushed to GitHub or the AWS stack has been applied.

## M1 · Application (10)

| Criterion | Evidence |
|---|---|
| FastAPI starts and answers `/health` | [`backend/app/main.py`](../backend/app/main.py) · [m9-metrics-endpoint.png](screenshots/m9-metrics-endpoint.png) (shows `/health` + `/ready`) |
| ≥ 4 REST endpoints (GET/POST/PUT/DELETE) | 11 endpoints, see the API table in the [README](../README.md#api) · [m1-swagger-docs.png](screenshots/m1-swagger-docs.png) |
| Postgres table managed by Alembic | [`0001_create_products.py`](../backend/alembic/versions/0001_create_products.py), [`0002_create_stock_movements.py`](../backend/alembic/versions/0002_create_stock_movements.py) · migrations visible in [m4-docker-compose-up.png](screenshots/m4-docker-compose-up.png) |
| Frontend renders and calls the API | [m1-app-localhost-3000.png](screenshots/m1-app-localhost-3000.png) · [m1-app-add-product.png](screenshots/m1-app-add-product.png) |
| Responsive, usable UI | [m1-app-mobile.png](screenshots/m1-app-mobile.png) (390 px wide) |

## M2 · Testing (10)

| Criterion | Evidence |
|---|---|
| `pytest` runs without errors | [m2-pytest-passing.png](screenshots/m2-pytest-passing.png): 29 passed |
| ≥ 5 tests over ≥ 3 endpoints | 29 tests over all 11 endpoints plus the migration chain, in [`backend/tests/`](../backend/tests) |
| Test DB, not production | [`conftest.py`](../backend/tests/conftest.py) sets `sqlite+pysqlite:///:memory:` before the app is imported |
| `pytest.ini` / `conftest.py` | [`backend/pytest.ini`](../backend/pytest.ini), [`backend/tests/conftest.py`](../backend/tests/conftest.py) |

## M3 · Git & GitHub (5)

| Criterion | Evidence |
|---|---|
| Public repo URL | <https://github.com/RashiMalik02/shelfwise> |
| Meaningful commit messages, ≥ 10 commits | [m3-commit-history.png](screenshots/m3-commit-history.png) |
| `.gitignore` covers `.env`, `__pycache__`, `node_modules`, `.venv` | [`.gitignore`](../.gitignore) |

## M4 · Docker (10)

| Criterion | Evidence |
|---|---|
| `backend/Dockerfile` builds | [`backend/Dockerfile`](../backend/Dockerfile) · [m4-docker-compose-up.png](screenshots/m4-docker-compose-up.png) |
| Frontend multi-stage (Node → nginx) | [`frontend/Dockerfile`](../frontend/Dockerfile): `node:24-alpine` build stage → `nginx-unprivileged` runtime |
| Non-root images | [m4-compose-ps-nonroot.png](screenshots/m4-compose-ps-nonroot.png): `uid=10001(shelfwise)` and `uid=101(nginx)` |
| `docker compose up --build` starts all 3 services | [m4-docker-compose-up.png](screenshots/m4-docker-compose-up.png) · [m4-compose-ps-nonroot.png](screenshots/m4-compose-ps-nonroot.png) · browser at :3000: [m1-app-localhost-3000.png](screenshots/m1-app-localhost-3000.png) |

## M5 · CI/CD (15)

| Criterion | Evidence |
|---|---|
| Workflow file present | [`.github/workflows/ci-cd.yml`](../.github/workflows/ci-cd.yml) |
| Triggers on push to `main` | `on.push.branches: [main]` |
| pytest job fails the build | `backend-tests` job; `images` has `needs: [backend-tests, …]` |
| Frontend built in pipeline | `frontend-build` job |
| Images built for both | `images` job, matrix `[backend, frontend]` |
| Pushed to GHCR | `docker push ghcr.io/<owner>/shelfwise-<service>:<sha>` |
| SHA tags, not `latest` | tag is `${{ github.sha }}`; `latest` is never pushed |
| Green run | <https://github.com/RashiMalik02/shelfwise/actions/runs/38824356101> · [m5-actions-run-green.png](screenshots/m5-actions-run-green.png) |
| GHCR with SHA tags | [m5-ghcr-backend-sha-tag.png](screenshots/m5-ghcr-backend-sha-tag.png) · [m5-ghcr-frontend-sha-tag.png](screenshots/m5-ghcr-frontend-sha-tag.png) (GitHub's "Latest" badge marks the newest version; no `latest` tag exists) |

## M6 · Trivy (5)

| Criterion | Evidence |
|---|---|
| Scan on both images in CI | "Trivy scan" step in the `images` matrix job |
| Fails on HIGH/CRITICAL | `severity: HIGH,CRITICAL`, `exit-code: "1"` |
| Explain a CVE / clean result | [`docs/TRIVY.md`](TRIVY.md) · [m6-trivy-before-fix.png](screenshots/m6-trivy-before-fix.png) (4 HIGH, exit 1) · [m6-trivy-clean-local.png](screenshots/m6-trivy-clean-local.png) (clean, exit 0) |
| Trivy in a real pipeline run | [m6-trivy-ci-step.png](screenshots/m6-trivy-ci-step.png) (step log from run 38824356101, both images clean) |

## M7 · Terraform (15)

| Criterion | Evidence |
|---|---|
| Valid HCL in `terraform/` | [`terraform/`](../terraform) · [m7-terraform-init-validate-test.png](screenshots/m7-terraform-init-validate-test.png) |
| `terraform init` OK | same screenshot |
| VPC with ≥ 2 public subnets | `module "vpc"` in [`main.tf`](../terraform/main.tf); asserted in [`tests/infrastructure.tftest.hcl`](../terraform/tests/infrastructure.tftest.hcl) |
| EKS with a node group | `module "eks"` → `eks_managed_node_groups.general` |
| `terraform.tfvars.example`, no secrets | [`terraform.tfvars.example`](../terraform/terraform.tfvars.example); `terraform.tfvars` and state are git-ignored |
| **Still to do (needs an AWS account that may create EC2/VPC/EKS)** | `terraform plan` screenshot · AWS Console VPC + EKS screenshot (ap-south-1) · `terraform destroy` screenshot |

> **AWS status (16 Oct 2026):** the AWS account `496159213908` is a member of an AWS Organization whose service control policies deny `ec2:*Vpc*`, `ec2:DescribeAvailabilityZones`, `eks:*` and `ssm:GetParameter` in every region. That even blocks `terraform plan`. No resources were created and no credits were used. Once the organization's administrator lifts those SCPs, or the account leaves the organization, run [`scripts/aws-capstone.sh`](../scripts/aws-capstone.sh).

## M8 · Kubernetes + Helm (15)

| Criterion | Evidence |
|---|---|
| `k8s/namespace.yaml` | [`k8s/namespace.yaml`](../k8s/namespace.yaml) · first command in [m8-kubectl-pods-svc-helm.png](screenshots/m8-kubectl-pods-svc-helm.png) |
| Chart with Chart.yaml, values, templates | [`helm/shelfwise/`](../helm/shelfwise) |
| `helm upgrade --install` works | [`scripts/deploy-local.sh`](../scripts/deploy-local.sh) · `helm list` in [m8-kubectl-pods-svc-helm.png](screenshots/m8-kubectl-pods-svc-helm.png) |
| ≥ 2 replicas each | frontend 2/2, backend 2 → 6 under load (HPA) |
| ClusterIP Services | `kubectl get svc` in the same screenshot |
| Ingress `/` → frontend, `/api` → backend | [`templates/ingress.yaml`](../helm/shelfwise/templates/ingress.yaml) · [m8-app-via-ingress.png](screenshots/m8-app-via-ingress.png) (http://shelfwise.localtest.me) |
| All pods Running | [m8-kubectl-pods-svc-helm.png](screenshots/m8-kubectl-pods-svc-helm.png) |
| Extra: HPA scaling | [m8-hpa-scaling.png](screenshots/m8-hpa-scaling.png): 4% → 449% CPU, 2 → 6 replicas |
| Extra: troubleshooting | [m8-troubleshooting-labs.png](screenshots/m8-troubleshooting-labs.png) · [`troubleshooting/README.md`](../troubleshooting/README.md) |

## M9 · Observability (10)

| Criterion | Evidence |
|---|---|
| `/metrics` in Prometheus format | [m9-metrics-endpoint.png](screenshots/m9-metrics-endpoint.png) |
| Prometheus scraping the app | [m9-prometheus-targets-up.png](screenshots/m9-prometheus-targets-up.png): `serviceMonitor/shelfwise/shelfwise-backend/0` 6/6 UP |
| Grafana installed | [`monitoring/kube-prometheus-stack-values.yaml`](../monitoring/kube-prometheus-stack-values.yaml) |
| Panel with live app metrics | [m9-grafana-dashboard.png](screenshots/m9-grafana-dashboard.png): req/s, p95 latency, status codes, stock movements, HPA replicas |

## M10 · Presentation (5)

| Criterion | Evidence |
|---|---|
| README explaining the app | [`README.md`](../README.md) |
| Live demo: commit → pipeline → deployment updates | Run-sheet in [`docs/DEMO.md`](DEMO.md). Rehearsed end to end: push `bd4fffe` → [run 38913787029](https://github.com/RashiMalik02/shelfwise/actions/runs/38913787029) green → bot commit `b73ec3b` → Argo CD synced: [m10-argocd-synced-healthy.png](screenshots/m10-argocd-synced-healthy.png) · header shows the new build: [m10-app-new-build-sha.png](screenshots/m10-app-new-build-sha.png) · pods rolling to the new tag: [m10-rollout.png](screenshots/m10-rollout.png) |

## Before you submit

```text
[ ] git push -u origin main, and the first pipeline run is green
[ ] GHCR packages made public (needed for the kind cluster / Argo CD to pull them)
[ ] Screenshots: Actions run, Trivy step log, GHCR package with SHA tag, GitHub commit history
[ ] AWS: terraform plan / console (VPC + EKS) / terraform destroy screenshots
[ ] terraform destroy actually finished (check EC2 → Load Balancers and NAT Gateways are empty)
```
