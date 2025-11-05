"""Retrieval utilities: vector search, BM25 fallback, and context assembly.

This module provides a small, testable surface used by the chat endpoint:
- `vector_search` queries Supabase via `supabase_client.search_similar_documents` and
  converts results into `RetrievedDocument` objects.
- `bm25_search` is a lightweight fallback to full-text search (mocked in tests).
- `assemble_context` orders retrieved docs by similarity and trims them to a
  token budget using `server.utils.count_tokens`.
"""
from typing import List, Tuple, Optional
import logging

from server import supabase_client
from server.models import RetrievedDocument
from server.utils import count_tokens, estimate_prompt_tokens
from server.config import get_config

logger = logging.getLogger(__name__)


def _trim_content_for_budget(content: str, allowed_tokens: int, model: str = "gpt-4o") -> Tuple[str, int]:
    """Trim content to fit into allowed_tokens while trying to preserve code fences and headings.

    This is a conservative, best-effort approach:
    - Prefer to not cut inside triple-backtick fences. If must, cut before the fence.
    - Trim by characters using a rough tokens->chars ratio (4 chars per token).
    Returns trimmed content and estimated token_count.
    """
    if allowed_tokens <= 0:
        return ("", 0)

    approx_chars = allowed_tokens * 4

    # If content is already short, return as-is
    if len(content) <= approx_chars:
        return (content, count_tokens(content, model=model))

    # Try to avoid cutting inside code fences: find first fence after the allowed window
    window = content[:approx_chars]
    # If window ends inside a fence, step back to the previous fence boundary
    last_open = window.rfind("```")
    if last_open != -1 and content.find("```", last_open + 3) != -1:
        # There's an open fence that continues past the window; cut before it
        cut_point = last_open
        trimmed = content[:cut_point]
    else:
        # Safe to cut at nearest newline before approx_chars
        nl = window.rfind("\n")
        if nl > int(approx_chars * 0.5):
            trimmed = content[:nl]
        else:
            trimmed = window

    return (trimmed.rstrip(), count_tokens(trimmed, model=model))


def vector_search(query_embedding: List[float], top_k: Optional[int] = None) -> List[RetrievedDocument]:
    """Perform a vector similarity search and return `RetrievedDocument`s.

    Args:
        query_embedding: Query vector
        top_k: Number of neighbors to return (defaults to config.retrieval_top_k)

    Returns:
        List of RetrievedDocument ordered by descending similarity_score
    """
    config = get_config()
    top_k = top_k or config.retrieval_top_k

    rows = supabase_client.search_similar_documents(query_embedding, limit=top_k)

    results: List[RetrievedDocument] = []
    for r in rows:
        # Expecting r to contain id, content, source_filename, chunk_index, token_count and similarity
        rd = RetrievedDocument(
            id=r.get("id"),
            content=r.get("content", ""),
            source_filename=r.get("source_filename", ""),
            chunk_index=r.get("chunk_index", 0),
            token_count=int(r.get("token_count", 0)),
            similarity_score=float(r.get("similarity", r.get("similarity_score", 0.0))),
            excerpt=(r.get("content", "")[:250] if r.get("content") else "")
        )
        results.append(rd)

    # Order by similarity descending (higher = more similar)
    results.sort(key=lambda x: x.similarity_score, reverse=True)
    logger.debug(f"vector_search returning {len(results)} documents")
    return results


def bm25_search(query: str, top_k: Optional[int] = None) -> List[RetrievedDocument]:
    """Fallback full-text search against Supabase documents table.

    This function is intentionally simple and is primarily intended for tests
    and cold-start scenarios. It uses the Supabase client directly.
    """
    config = get_config()
    top_k = top_k or config.retrieval_top_k

    client = supabase_client.init_supabase_client()
    try:
        # Use Postgres full-text search via `plainto_tsquery` in a RPC or raw SQL.
        # For testability we keep this high-level and let tests mock the client.
        result = client.table(config.rag_vector_table).select("*").text_search(
            "content", query, config="english"
        ).limit(top_k).execute()

        rows = result.data if result.data else []
        docs: List[RetrievedDocument] = []
        for r in rows:
            docs.append(RetrievedDocument(
                id=r.get("id"),
                content=r.get("content", ""),
                source_filename=r.get("source_filename", ""),
                chunk_index=r.get("chunk_index", 0),
                token_count=int(r.get("token_count", 0)),
                similarity_score=float(r.get("rank", 0.0)),
                excerpt=(r.get("content", "")[:250] if r.get("content") else "")
            ))

        docs.sort(key=lambda x: x.similarity_score, reverse=True)
        return docs

    except Exception as e:
        logger.warning("bm25_search failed: %s", e)
        return []


def assemble_context(
    retrieved: List[RetrievedDocument],
    token_budget: Optional[int] = None,
    model: str = "gpt-4o"
) -> Tuple[List[RetrievedDocument], int]:
    """Pick top documents and trim them to respect the token budget.

    Args:
        retrieved: List of RetrievedDocument (ordered by similarity)
        token_budget: Maximum token budget for the assembled prompt (prompt only)
        model: Model name to use for token estimation

    Returns:
        (selected_documents, tokens_used)
    """
    config = get_config()
    token_budget = token_budget or config.prompt_token_budget

    selected: List[RetrievedDocument] = []
    tokens_used = 0

    for doc in retrieved:
        # conservative estimate per doc
        doc_tokens = int(doc.token_count or count_tokens(doc.content, model=model))

        if tokens_used + doc_tokens > token_budget:
            # if no docs selected yet, try to include a trimmed version fitting the budget
            if not selected:
                remaining = token_budget - tokens_used
                trimmed_content, trimmed_tokens = _trim_content_for_budget(doc.content, remaining, model=model)
                if trimmed_tokens > 0:
                    trimmed_doc = RetrievedDocument(
                        **{**doc.model_dump(), "content": trimmed_content, "token_count": trimmed_tokens}
                    )
                    selected.append(trimmed_doc)
                    tokens_used += trimmed_tokens
            break

        selected.append(doc)
        tokens_used += doc_tokens

        if tokens_used >= token_budget:
            break

    logger.debug(f"assemble_context selected {len(selected)} docs using {tokens_used} tokens")
    return selected, tokens_used


def hybrid_search(query_embedding: List[float], query_text: str, top_k: Optional[int] = None) -> List[RetrievedDocument]:
    """Combine vector and BM25 results into a single ranked list.

    Strategy:
    - Fetch top_k vector results and top_k BM25 results.
    - Normalize scores to 0-1 per-method and combine with weighted sum.
    - Return merged list ordered by combined score.
    """
    config = get_config()
    top_k = top_k or config.retrieval_top_k

    vec = vector_search(query_embedding, top_k=top_k)
    bm25 = bm25_search(query_text, top_k=top_k)

    combined = {}

    # Normalize vector scores
    max_vec = max((d.similarity_score for d in vec), default=0.0)
    for d in vec:
        norm = (d.similarity_score / max_vec) if max_vec > 0 else d.similarity_score
        combined[d.id] = {
            "doc": d,
            "vec_score": norm,
            "bm25_score": 0.0
        }

    # Normalize bm25 scores (they may be 'rank' style; treat relative)
    max_b = max((d.similarity_score for d in bm25), default=0.0)
    for d in bm25:
        norm = (d.similarity_score / max_b) if max_b > 0 else d.similarity_score
        if d.id in combined:
            combined[d.id]["bm25_score"] = norm
        else:
            combined[d.id] = {"doc": d, "vec_score": 0.0, "bm25_score": norm}

    weight = config.hybrid_bm25_weight
    merged_list = []
    for val in combined.values():
        score = (1 - weight) * val["vec_score"] + weight * val["bm25_score"]
        doc = val["doc"]
        # attach combined score for sorting and provenance
        merged_doc = RetrievedDocument(**{**doc.model_dump(), "similarity_score": float(score)})
        merged_list.append(merged_doc)

    merged_list.sort(key=lambda x: x.similarity_score, reverse=True)
    return merged_list
