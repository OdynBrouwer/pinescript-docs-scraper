"""Integration-style API tests mocking Supabase/OpenAI interactions.

These tests patch the names imported into `server.app` so the endpoint
logic can be exercised without network calls.
"""
import time
from fastapi.testclient import TestClient
from server.app import app
import server.auth as server_auth

client = TestClient(app)


def test_chat_flow_success(monkeypatch):
    """Mock embeddings/retrieval/LLM and verify `/chat` returns structured data."""
    from server.models import RetrievedDocument

    # Dummy retrieved document
    dummy_doc = RetrievedDocument(
        id="d1",
        content="// example pine code\n//@version=6\nplot(close)",
        source_filename="processed_3_first-indicator_20251031_113440.md",
        chunk_index=0,
        token_count=12,
        similarity_score=0.92,
        excerpt="// example pine code"
    )

    # Patch functions imported into server.app
    monkeypatch.setattr("server.app.generate_single_embedding", lambda q: [0.0] * 1536)
    monkeypatch.setattr("server.app.hybrid_search", lambda emb, q, top_k: [dummy_doc])
    monkeypatch.setattr("server.app.assemble_context", lambda retrieved: ([dummy_doc], 12))
    # Configure a test HS256 secret and issue a token so real verification runs
    from jose import jwt as jose_jwt
    cfg = __import__("server.config", fromlist=["get_config"]).get_config()
    cfg.jwt_secret = "test-secret"
    cfg.jwt_algorithm = "HS256"
    token = jose_jwt.encode({"sub": "test-user"}, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)

    def fake_create_chat_completion(query, context_docs, temperature=0.1):
        return {
            "response": "To create an SMA...\n```pine\n//@version=6\n...```",
            "model": "gpt-4o",
            "tokens": {"prompt": 120, "completion": 40, "total": 160},
            "sources": [
                {"filename": "processed_3_first-indicator_20251031_113440.md", "similarity_score": 0.92, "excerpt": "// example pine code"}
            ]
        }

    monkeypatch.setattr("server.app.create_chat_completion", fake_create_chat_completion)

    resp = client.post(
        "/chat",
        json={"query": "How do I create a simple moving average?", "max_context_docs": 1, "temperature": 0.1},
        headers={"Authorization": f"Bearer {token}"}
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "response" in data
    assert isinstance(data["sources"], list)
    assert "tokens_used" in data
    assert data["model"] == "gpt-4o"


def test_trigger_index_background(monkeypatch):
    """Ensure `/internal/index` can schedule a background indexing task."""
    # Accept admin key
    monkeypatch.setattr("server.app.verify_admin_key", lambda k: True)

    # Replace indexing function with a fake async function that records invocation
    called = {"count": 0}

    async def fake_index_documents(full_reindex: bool = False):
        called["count"] += 1
        # simulate some work
        time.sleep(0.01)
        return {"success": True}

    monkeypatch.setattr("server.app.index_documents", fake_index_documents)

    resp = client.post(
        "/internal/index?background=true",
        headers={"X-Admin-Key": "admin-key"}
    )

    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data.get("started") is True
    assert data.get("background") is True

    # Give a tiny window for the background task to run
    time.sleep(0.05)
    assert called["count"] >= 1


def test_chat_auth_failure_no_token():
    """Requests without Authorization should be rejected (401 or 403)."""
    resp = client.post(
        "/chat",
        json={"query": "Will this be rejected?", "max_context_docs": 1, "temperature": 0.1}
    )
    assert resp.status_code in (401, 403)


def test_chat_rate_limit(monkeypatch):
    """Ensure rate limiting triggers 429 after exceeding allowed requests."""
    # Patch verification to accept any token so we can focus on rate limiting
    # Configure JWT secret and token for authenticating repeated requests
    from jose import jwt as jose_jwt
    cfg = __import__("server.config", fromlist=["get_config"]).get_config()
    cfg.jwt_secret = "test-secret"
    cfg.jwt_algorithm = "HS256"
    token = jose_jwt.encode({"sub": "test-user"}, cfg.jwt_secret, algorithm=cfg.jwt_algorithm)

    # Minimal LLM pipeline to return quickly
    from server.models import RetrievedDocument
    dummy_doc = RetrievedDocument(
        id="d1",
        content="x",
        source_filename="f.md",
        chunk_index=0,
        token_count=1,
        similarity_score=0.9,
        excerpt="x"
    )
    monkeypatch.setattr("server.app.generate_single_embedding", lambda q: [0.0] * 1536)
    monkeypatch.setattr("server.app.hybrid_search", lambda emb, q, top_k: [dummy_doc])
    monkeypatch.setattr("server.app.assemble_context", lambda retrieved: ([dummy_doc], 1))
    monkeypatch.setattr("server.app.create_chat_completion", lambda q, docs, temp=0.1: {"response": "ok", "model": "gpt-4o", "tokens": {"prompt": 1, "completion": 1, "total": 2}, "sources": []})

    headers = {"Authorization": f"Bearer {token}"}

    # The /chat endpoint is decorated with limit "10/minute" in app; send 12 requests
    statuses = []
    for i in range(12):
        resp = client.post(
            "/chat",
            json={"query": f"q{i}", "max_context_docs": 1, "temperature": 0.1},
            headers=headers
        )
        statuses.append(resp.status_code)

    # Expect at least one 429 (rate limited) and earlier requests succeeded
    assert 429 in statuses
