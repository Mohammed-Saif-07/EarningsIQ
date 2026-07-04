.PHONY: up up-detached down logs ingest process signals api frontend test sql demo-mode live-mode smoke test-imports screenshot-reminder k8s-up k8s-status k8s-logs k8s-down

up:
	test -f .env || cp .env.example .env
	docker compose up --build

up-detached:
	test -f .env || cp .env.example .env
	docker compose up -d --build

down:
	docker compose down

logs:
	docker compose logs -f

demo-mode:
	test -f .env || cp .env.example .env
	perl -0pi -e 's/^USE_LIVE_EDGAR=.*/USE_LIVE_EDGAR=false/m; s/^USE_FINBERT=.*/USE_FINBERT=false/m; s/^USE_KAFKA=.*/USE_KAFKA=false/m' .env
	docker compose up -d --force-recreate api frontend

live-mode:
	test -f .env || cp .env.example .env
	perl -0pi -e 's/^USE_LIVE_EDGAR=.*/USE_LIVE_EDGAR=true/m; s/^USE_FINBERT=.*/USE_FINBERT=true/m; s/^USE_KAFKA=.*/USE_KAFKA=true/m' .env
	docker compose up -d --force-recreate postgres redis zookeeper kafka api frontend

api:
	uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

frontend:
	cd frontend && npm install && npm run dev

ingest:
	docker compose exec -T api python -m agents.orchestrator --ticker $(or $(TICKER),AAPL) --emit-kafka

process:
	docker compose exec -T api python -m agents.orchestrator --ticker $(or $(TICKER),AAPL)

signals:
	docker compose exec -T api python -m agents.orchestrator --ticker $(or $(TICKER),AAPL)

sql:
	docker compose exec -T postgres psql -U earningsiq -d earningsiq -f /docker-entrypoint-initdb.d/01_schema.sql -f /docker-entrypoint-initdb.d/02_indexes.sql -f /docker-entrypoint-initdb.d/03_partitioning.sql -f /docker-entrypoint-initdb.d/04_views.sql -f /docker-entrypoint-initdb.d/05_materialized_views.sql -f /docker-entrypoint-initdb.d/06_functions.sql -f /docker-entrypoint-initdb.d/07_triggers.sql -f /docker-entrypoint-initdb.d/08_seed_data.sql

# ── Testing ────────────────────────────────────────────────
smoke:
	@bash smoke_test.sh

test:
	@docker compose exec -T api pytest tests/test_smoke.py -v --tb=short

test-imports:
	@docker compose exec -T api pytest tests/test_smoke.py -v -k "import" --tb=short

# ── Screenshots helper ─────────────────────────────────────
screenshot-reminder:
	@echo ""
	@echo "📸 Screenshot checklist:"
	@echo "  1. make up"
	@echo "  2. make ingest TICKER=AAPL"
	@echo "  3. Open http://localhost:5173"
	@echo "  4. Save screenshots to screenshots/ folder"
	@echo "  5. git add screenshots/ && git commit -m 'add screenshots'"
	@echo ""

k8s-up:
	kubectl apply -f k8s/namespace.yaml
	kubectl apply -f k8s/configmap.yaml
	kubectl apply -f k8s/secrets.yaml
	kubectl apply -f k8s/postgres/
	kubectl apply -f k8s/kafka/
	kubectl apply -f k8s/redis/
	kubectl apply -f k8s/agents/
	kubectl apply -f k8s/api/
	kubectl apply -f k8s/frontend/

k8s-status:
	kubectl get pods -n earningsiq

k8s-logs:
	kubectl logs -f deployment/$(or $(AGENT),watcher)-agent -n earningsiq

k8s-down:
	kubectl delete namespace earningsiq
