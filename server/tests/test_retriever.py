import pytest

from server.retriever import assemble_context, vector_search
from server.models import RetrievedDocument


def make_doc(i: int, tokens: int, sim: float) -> RetrievedDocument:
    return RetrievedDocument(
        id=f"doc{i}",
        content=("x" * (tokens * 4)),  # approx chars
        source_filename=f"file{i}.md",
        chunk_index=0,
        token_count=tokens,
        similarity_score=sim,
        excerpt=("x" * 50)
    )


def test_assemble_context_respects_budget():
    docs = [make_doc(1, 1000, 0.9), make_doc(2, 800, 0.8), make_doc(3, 600, 0.7)]

    selected, tokens_used = assemble_context(docs, token_budget=1500, model="gpt-4o")

    # Should include first doc (1000) and then second doc (800) would exceed budget,
    # so only the first should be selected (or a trimmed piece if none fit)
    assert len(selected) >= 1
    assert tokens_used <= 1500
    assert selected[0].id == "doc1"


def test_vector_search_conversion(monkeypatch):
    fake_rows = [
        {"id": "a", "content": "hello a", "source_filename": "a.md", "chunk_index": 0, "token_count": 50, "similarity": 0.95},
        {"id": "b", "content": "hello b", "source_filename": "b.md", "chunk_index": 0, "token_count": 60, "similarity": 0.9}
    ]

    def fake_search(q, limit=12):
        assert isinstance(q, list)
        return fake_rows

    monkeypatch.setattr("server.supabase_client.search_similar_documents", fake_search)

    results = vector_search([0.1, 0.2, 0.3], top_k=2)
    assert len(results) == 2
    assert results[0].id == "a"
    assert results[1].id == "b"


def test_hybrid_search_merging(monkeypatch):
    # Make vector and bm25 return overlapping and distinct docs
    vec_rows = [
        {"id": "a", "content": "a", "source_filename": "a.md", "chunk_index": 0, "token_count": 50, "similarity": 0.95},
        {"id": "b", "content": "b", "source_filename": "b.md", "chunk_index": 0, "token_count": 60, "similarity": 0.9}
    ]
    bm25_rows = [
        {"id": "b", "content": "b", "source_filename": "b.md", "chunk_index": 0, "token_count": 60, "similarity": 2.0},
        {"id": "c", "content": "c", "source_filename": "c.md", "chunk_index": 0, "token_count": 40, "similarity": 1.5}
    ]

    monkeypatch.setattr("server.supabase_client.search_similar_documents", lambda q, limit=12: vec_rows)
    # For bm25, patch the supabase client table call used by bm25_search
    class FakeQuery:
        def __init__(self, data):
            self.data = data
        def select(self, *args, **kwargs):
            return self
        def text_search(self, *args, **kwargs):
            return self
        def limit(self, *args, **kwargs):
            return self
        def execute(self):
            return self

    class FakeClient:
        def table(self, t):
            return FakeQuery(bm25_rows)

    monkeypatch.setattr("server.retriever.supabase_client.init_supabase_client", lambda: FakeClient())

    from server.retriever import hybrid_search

    merged = hybrid_search([0.1, 0.2], "query", top_k=3)
    # Should include docs a, b, c and be sorted
    ids = [d.id for d in merged]
    assert set(ids) == {"a", "b", "c"}
