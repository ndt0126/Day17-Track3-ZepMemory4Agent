from __future__ import annotations

from typing import Any

from .config import settings
from .context_budget import ContextBudgetManager
from .utils import cap_query
from .zep_common import prime_eval_thread, render_graph_search


class StudentMemory:
    """Only this file needs to be edited by students."""

    def __init__(self, client: Any):
        self.client = client
        self.budget = ContextBudgetManager(settings.context_tokens)

    def retrieve_long_term(self, user_id: str, thread_id: str, query: str) -> str:
        # LAB TODO 1/4 — Context Block retrieval
        prime_eval_thread(self.client, user_id, thread_id, query)
        context = self.client.thread.get_user_context(thread_id=thread_id)
        return context.context or ""

    def retrieve_episodic(self, user_id: str, query: str) -> str:
        # LAB TODO 2/4 — Episode search on user graph
        results = self.client.graph.search(
            user_id=user_id,
            query=cap_query(query),
            scope="episodes",
            limit=5,
        )
        return render_graph_search(results, episode_char_cap=1500)

    def retrieve_semantic(self, graph_id: str, query: str) -> str:
        # LAB TODO 3/4 — Semantic search on standalone shared graph
        try:
            results = self.client.graph.search(
                graph_id=graph_id,
                query=cap_query(query),
                scope="episodes",
                limit=8,
            )
            text = render_graph_search(results)
            if text.strip():
                return text
        except Exception:
            pass
        # Fallback: scope="nodes"
        results = self.client.graph.search(
            graph_id=graph_id,
            query=cap_query(query),
            scope="nodes",
            limit=8,
        )
        return render_graph_search(results)

    def assemble_context(self, layers: dict[str, str]) -> tuple[str, dict[str, dict[str, int]]]:
        # LAB TODO 4/4 — Budget 10/4/3/3, priority STM→LT→EP→SEM
        return self.budget.assemble(layers)
