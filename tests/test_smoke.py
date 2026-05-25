"""
EarningsIQ — Python Smoke Tests
Built by Saif Mohammed · smohammed8@seattleu.edu
Run: pytest tests/test_smoke.py -v
"""

import importlib
import pytest
import os


# --------------------------------------------------------
# Module import tests
# --------------------------------------------------------

MODULES = [
    "agents.state",
    "agents.orchestrator",
    "agents.watcher_agent",
    "agents.ingest_agent",
    "agents.nlp_agent",
    "agents.research_agent",
    "agents.report_agent",
    "agents.qa_agent",
    "ingestion.edgar_client",
    "ingestion.transcript_parser",
    "ingestion.kafka_producer",
    "stream.consumer",
    "stream.sentiment_processor",
    "ml.anomaly_detector",
    "ml.price_correlator",
    "ml.signal_ranker",
    "llm.groq_client",
    "llm.ollama_client",
    "llm.qa_engine",
    "api.main",
]

@pytest.mark.parametrize("module", MODULES)
def test_module_imports(module):
    """Every module must import without raising an exception."""
    mod = importlib.import_module(module)
    assert mod is not None, f"Module {module} imported as None"


# --------------------------------------------------------
# State schema test
# --------------------------------------------------------

def test_agent_state_schema():
    """AgentState must have all required keys."""
    from agents.state import AgentState
    required_keys = {
        "filing_id", "ticker", "quarter", "year",
        "transcript_text", "chunks", "sentiment_scores",
        "anomalies", "company_context", "signal_report",
        "price_delta_1d", "price_delta_5d", "error", "step",
    }
    annotations = AgentState.__annotations__
    missing = required_keys - set(annotations.keys())
    assert not missing, f"AgentState missing keys: {missing}"


# --------------------------------------------------------
# EDGAR client test
# --------------------------------------------------------

def test_edgar_client_has_required_functions():
    """edgar_client must expose get_recent_filings and fetch_transcript_text."""
    from ingestion import edgar_client
    assert callable(getattr(edgar_client, "get_recent_filings", None)), \
        "get_recent_filings not found"
    assert callable(getattr(edgar_client, "fetch_transcript_text", None)), \
        "fetch_transcript_text not found"


# --------------------------------------------------------
# Anomaly detector test
# --------------------------------------------------------

def test_anomaly_detector_zscore():
    """anomaly_detector must flag a clearly anomalous score."""
    from ml.anomaly_detector import detect_anomalies

    # 9 neutral sentences + 1 very negative one
    scores = [0.1, 0.2, 0.15, 0.05, 0.18, 0.12, 0.09, 0.22, 0.17, -0.95]
    texts  = [f"Sentence {i}" for i in range(len(scores))]

    anomalies = detect_anomalies(scores, texts)
    assert len(anomalies) >= 1, "Expected at least 1 anomaly for clearly negative score"
    assert anomalies[-1]["sentence_index"] == 9, "Last sentence should be flagged"


# --------------------------------------------------------
# Signal score function test
# --------------------------------------------------------

def test_signal_score_bounds():
    """compute_signal_score must return a value between 0 and 100."""
    from ml.signal_ranker import compute_signal_score

    score = compute_signal_score(
        anomaly_count=3,
        high_severity=1,
        sentiment_mean=-0.4,
        price_delta_1d=5.2
    )
    assert 0 <= score <= 100, f"signal_score {score} out of bounds [0, 100]"


# --------------------------------------------------------
# FastAPI routes test
# --------------------------------------------------------

def test_fastapi_app_loads():
    """FastAPI app must be importable and have expected routes."""
    from api.main import app
    routes = [r.path for r in app.routes]
    assert "/" in routes,            "Missing root route GET /"
    assert "/health" in routes,      "Missing /health route"


def test_fastapi_root_attribution():
    """GET / must return attribution fields."""
    from fastapi.testclient import TestClient
    from api.main import app

    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data.get("built_by") == "Saif Mohammed", \
        f"built_by field wrong: {data.get('built_by')}"
    assert "smohammed8@seattleu.edu" in data.get("contact", ""), \
        f"contact field missing email: {data.get('contact')}"


# --------------------------------------------------------
# .env.example completeness test
# --------------------------------------------------------

def test_env_example_has_required_keys():
    """Every required env key must exist in .env.example."""
    required = [
        "POSTGRES_USER", "POSTGRES_PASSWORD", "POSTGRES_DB",
        "DATABASE_URL", "KAFKA_BOOTSTRAP_SERVERS", "KAFKA_TOPIC_RAW",
        "LLM_PROVIDER", "GROQ_API_KEY", "SEC_USER_AGENT",
        "API_PORT", "FRONTEND_PORT",
    ]
    env_example_path = os.path.join(
        os.path.dirname(__file__), "..", ".env.example"
    )
    with open(env_example_path) as f:
        content = f.read()
    missing = [k for k in required if k not in content]
    assert not missing, f".env.example missing keys: {missing}"


# --------------------------------------------------------
# SQL files completeness test
# --------------------------------------------------------

def test_sql_files_exist():
    """All 8 SQL files must be present."""
    sql_dir = os.path.join(os.path.dirname(__file__), "..", "sql")
    expected = [
        "01_schema.sql", "02_indexes.sql", "03_partitioning.sql",
        "04_views.sql", "05_materialized_views.sql", "06_functions.sql",
        "07_triggers.sql", "08_seed_data.sql",
    ]
    missing = [f for f in expected
               if not os.path.exists(os.path.join(sql_dir, f))]
    assert not missing, f"Missing SQL files: {missing}"


# --------------------------------------------------------
# K8s manifests test
# --------------------------------------------------------

def test_k8s_agent_manifests_exist():
    """All 5 agent K8s manifests must be present."""
    k8s_agents = os.path.join(os.path.dirname(__file__), "..", "k8s", "agents")
    expected = [
        "watcher-agent.yaml", "ingest-agent.yaml", "nlp-agent.yaml",
        "research-agent.yaml", "report-agent.yaml",
    ]
    missing = [f for f in expected
               if not os.path.exists(os.path.join(k8s_agents, f))]
    assert not missing, f"Missing K8s agent manifests: {missing}"


def test_k8s_namespace_has_owner_label():
    """namespace.yaml must have owner: saif-mohammed label."""
    import yaml
    ns_path = os.path.join(
        os.path.dirname(__file__), "..", "k8s", "namespace.yaml"
    )
    with open(ns_path) as f:
        manifest = yaml.safe_load(f)
    labels = manifest.get("metadata", {}).get("labels", {})
    assert labels.get("owner") == "saif-mohammed", \
        f"namespace.yaml missing owner label: {labels}"
