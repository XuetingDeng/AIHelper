from eval.metrics import (
    cohens_kappa,
    expected_fact_recall,
    forbidden_fact_violation,
    tool_routing_accuracy,
)


def test_eval_metrics():
    output = {"summary": "Notion recruiter Software Engineer", "items": []}
    assert expected_fact_recall(output, ["Notion", "Software Engineer"]) == 1.0
    assert forbidden_fact_violation(output, ["email sent"]) == 0.0
    assert tool_routing_accuracy(["search_emails"], ["search_emails", "read_notes"]) == 0.5
    assert cohens_kappa(["pass", "fail"], ["pass", "fail"]) == 1.0
