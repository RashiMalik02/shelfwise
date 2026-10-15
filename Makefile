.PHONY: test lint up down kind deploy load tf-check

test:            ## backend + frontend tests
	cd backend && .venv/bin/pytest -v
	cd frontend && npm test

lint:
	cd backend && .venv/bin/ruff check . && .venv/bin/ruff format --check .
	helm lint helm/shelfwise -f helm/shelfwise/values-local.yaml

up:              ## full stack in docker compose
	docker compose up --build

down:
	docker compose down

kind:            ## local cluster with ingress + monitoring
	./scripts/kind-up.sh

deploy:          ## build, load into kind, helm upgrade
	./scripts/deploy-local.sh

load:            ## drive the HPA
	./scripts/load-test.sh 180

tf-check:        ## terraform checks that need no AWS account
	cd terraform && terraform fmt -check -recursive && terraform init -backend=false -input=false >/dev/null && terraform validate && terraform test
