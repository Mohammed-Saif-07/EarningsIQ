#!/usr/bin/env bash
# ============================================================
# EarningsIQ — Smoke Test
# Built by Saif Mohammed · smohammed8@seattleu.edu
# Usage: bash smoke_test.sh
# ============================================================

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

pass() { echo -e "${GREEN}✓ PASS${NC} — $1"; PASS=$((PASS + 1)); }
fail() { echo -e "${RED}✗ FAIL${NC} — $1"; FAIL=$((FAIL + 1)); }
info() { echo -e "${YELLOW}→${NC} $1"; }

echo ""
echo "========================================"
echo "  EarningsIQ Smoke Test"
echo "  Built by Saif Mohammed"
echo "  smohammed8@seattleu.edu"
echo "========================================"
echo ""

# --------------------------------------------------------
# CHECK 1 — Docker running
# --------------------------------------------------------
info "Checking Docker..."
if docker info > /dev/null 2>&1; then
    pass "Docker is running"
else
    fail "Docker is not running — start Docker Desktop first"
    exit 1
fi

# --------------------------------------------------------
# CHECK 2 — .env file exists
# --------------------------------------------------------
info "Checking .env file..."
if [ -f ".env" ]; then
    pass ".env file exists"
else
    fail ".env file missing — run: cp .env.example .env"
    exit 1
fi

# --------------------------------------------------------
# CHECK 3 — Docker Compose up
# --------------------------------------------------------
info "Starting services with docker compose..."
docker compose up -d --quiet-pull 2>/dev/null
sleep 10
pass "docker compose up completed"

# --------------------------------------------------------
# CHECK 4 — PostgreSQL reachable
# --------------------------------------------------------
info "Checking PostgreSQL..."
if docker compose exec -T postgres pg_isready -U earningsiq > /dev/null 2>&1; then
    pass "PostgreSQL is ready"
else
    fail "PostgreSQL not reachable"
fi

# --------------------------------------------------------
# CHECK 5 — Kafka broker reachable
# --------------------------------------------------------
info "Checking Kafka..."
if docker compose exec -T kafka kafka-topics \
    --bootstrap-server kafka:9092 --list > /dev/null 2>&1; then
    pass "Kafka broker is reachable"
else
    fail "Kafka broker not reachable"
fi

# --------------------------------------------------------
# CHECK 6 — Redis reachable
# --------------------------------------------------------
info "Checking Redis..."
if docker compose exec -T redis redis-cli ping | grep -q "PONG"; then
    pass "Redis is reachable"
else
    fail "Redis not reachable"
fi

# --------------------------------------------------------
# CHECK 7 — FastAPI health endpoint
# --------------------------------------------------------
info "Checking FastAPI /health..."
sleep 5
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || true)
if [ "$HTTP_STATUS" = "200" ]; then
    pass "FastAPI /health returned 200"
else
    fail "FastAPI /health returned HTTP $HTTP_STATUS"
fi

# --------------------------------------------------------
# CHECK 8 — FastAPI root attribution
# --------------------------------------------------------
info "Checking FastAPI / attribution..."
ROOT_RESPONSE=$(curl -s http://localhost:8000/ || true)
if echo "$ROOT_RESPONSE" | grep -q "Saif Mohammed"; then
    pass "FastAPI root response contains attribution"
else
    fail "FastAPI root response missing attribution"
fi

# --------------------------------------------------------
# CHECK 9 — Frontend reachable
# --------------------------------------------------------
info "Checking frontend..."
FRONTEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5173 || true)
if [ "$FRONTEND_STATUS" = "200" ]; then
    pass "Frontend at localhost:5173 returned 200"
else
    fail "Frontend not reachable — HTTP $FRONTEND_STATUS"
fi

# --------------------------------------------------------
# CHECK 10 — SQL tables exist
# --------------------------------------------------------
info "Checking SQL schema..."
TABLE_COUNT=$(docker compose exec -T postgres psql -U earningsiq -d earningsiq -t -c \
    "SELECT COUNT(*) FROM information_schema.tables
     WHERE table_schema = 'public';" 2>/dev/null | tr -d ' ')

if [ "$TABLE_COUNT" -ge "8" ]; then
    pass "SQL schema has $TABLE_COUNT tables (expected ≥ 8)"
else
    fail "SQL schema only has $TABLE_COUNT tables — run init.sql"
fi

# --------------------------------------------------------
# CHECK 11 — Materialized views exist
# --------------------------------------------------------
info "Checking materialized views..."
MV_COUNT=$(docker compose exec -T postgres psql -U earningsiq -d earningsiq -t -c \
    "SELECT COUNT(*) FROM pg_matviews WHERE schemaname='public';" 2>/dev/null | tr -d ' ')

if [ "$MV_COUNT" -ge "2" ]; then
    pass "Materialized views present ($MV_COUNT found)"
else
    fail "Materialized views missing ($MV_COUNT found)"
fi

# --------------------------------------------------------
# CHECK 12 — Seed data loaded
# --------------------------------------------------------
info "Checking seed data..."
COMPANY_COUNT=$(docker compose exec -T postgres psql -U earningsiq -d earningsiq -t -c \
    "SELECT COUNT(*) FROM companies;" 2>/dev/null | tr -d ' ')

if [ "$COMPANY_COUNT" -ge "5" ]; then
    pass "Seed data loaded ($COMPANY_COUNT companies)"
else
    fail "Seed data missing ($COMPANY_COUNT companies found)"
fi

# --------------------------------------------------------
# CHECK 13 — Python imports
# --------------------------------------------------------
info "Checking Python imports..."
if python3 -c "
import agents, ingestion, stream, ml, llm, api, pipeline
print('all imports ok')
" > /dev/null 2>&1; then
    pass "All Python modules import without error"
else
    fail "Python import error — check requirements.txt and __init__.py files"
fi

# --------------------------------------------------------
# CHECK 14 — Kafka topic created
# --------------------------------------------------------
info "Checking Kafka topic earnings-raw..."
TOPICS=$(docker compose exec -T kafka kafka-topics \
    --bootstrap-server kafka:9092 --list 2>/dev/null || true)
if echo "$TOPICS" | grep -q "earnings-raw"; then
    pass "Kafka topic 'earnings-raw' exists"
else
    fail "Kafka topic 'earnings-raw' missing"
fi

# --------------------------------------------------------
# CHECK 15 — .env has no placeholder values
# --------------------------------------------------------
info "Checking .env for unfilled placeholders..."
if grep -q "your_groq_api_key_here" .env; then
    fail ".env still has placeholder GROQ_API_KEY — fill it in or set LLM_PROVIDER=ollama"
else
    pass ".env has no unfilled placeholders"
fi

# --------------------------------------------------------
# SUMMARY
# --------------------------------------------------------
echo ""
echo "========================================"
TOTAL=$((PASS + FAIL))
echo "  Results: $PASS/$TOTAL passed"
if [ "$FAIL" -eq 0 ]; then
    echo -e "  ${GREEN}All checks passed — EarningsIQ is healthy ✓${NC}"
else
    echo -e "  ${RED}$FAIL check(s) failed — see above${NC}"
fi
echo ""
echo "  Built by Saif Mohammed · smohammed8@seattleu.edu"
echo "========================================"
echo ""
exit $FAIL
