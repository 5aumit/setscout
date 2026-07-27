from __future__ import annotations

from setscout.graph.nodes.evaluator import node_evaluator
from setscout.models import (
    CandidateEvaluation,
    DatasetCandidate,
    PipelineResult,
    SearchSpec,
    UserQuery,
)


class _FailingStructuredOutput:
    def invoke(self, prompt: str):
        raise RuntimeError("provider unavailable")


class _FailingLlm:
    def with_structured_output(self, schema):
        return _FailingStructuredOutput()


class _StructuredOutput:
    def __init__(self, result: PipelineResult):
        self.result = result

    def invoke(self, prompt: str) -> PipelineResult:
        return self.result


class _Llm:
    def __init__(self, result: PipelineResult):
        self.result = result

    def with_structured_output(self, schema):
        return _StructuredOutput(self.result)


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


def test_evaluator_repairs_duplicate_ranks_from_an_otherwise_complete_response():
    candidates = [
        DatasetCandidate(
            id=f"candidate-{number}",
            source="huggingface",
            name=f"Candidate {number}",
            url=f"https://example.com/candidate-{number}",
        )
        for number in (1, 2, 3)
    ]
    state = {
        "query": UserQuery(purpose="classify", domain="NLP", data_type="text"),
        "search_spec": SearchSpec(expanded_keywords=["text"], prioritized_sources=["huggingface"]),
        "candidates": candidates,
    }
    response = PipelineResult(
        evaluations=[
            CandidateEvaluation(candidate_id="candidate-1", rank=1, fit_summary="First"),
            CandidateEvaluation(candidate_id="candidate-2", rank=1, fit_summary="Second"),
            CandidateEvaluation(candidate_id="candidate-3", rank=3, fit_summary="Third"),
        ],
        report_markdown="Overview",
    )

    patch = node_evaluator(state, llm=_Llm(response))

    assert [evaluation.candidate_id for evaluation in patch["evaluations"]] == [
        "candidate-1",
        "candidate-2",
        "candidate-3",
    ]
    assert [evaluation.rank for evaluation in patch["evaluations"]] == [1, 2, 3]
