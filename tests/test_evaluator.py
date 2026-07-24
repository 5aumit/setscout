from __future__ import annotations

from setscout.graph.nodes.evaluator import node_evaluator
from setscout.models import DatasetCandidate, SearchSpec, UserQuery


class _FailingStructuredOutput:
    def invoke(self, prompt: str):
        raise RuntimeError("provider unavailable")


class _FailingLlm:
    def with_structured_output(self, schema):
        return _FailingStructuredOutput()


def test_evaluator_failure_does_not_create_input_order_ranked_results():
    state = {
        "query": UserQuery(purpose="classify", domain="NLP", data_type="text"),
        "search_spec": SearchSpec(expanded_keywords=["text"], prioritized_sources=["huggingface"]),
        "candidates": [
            DatasetCandidate(
                id="candidate-1",
                source="huggingface",
                name="Candidate one",
                url="https://example.com/candidate-1",
            )
        ],
    }

    patch = node_evaluator(state, llm=_FailingLlm())

    assert patch["evaluation_failed"] is True
    assert "evaluations" not in patch
    assert "report" not in patch
