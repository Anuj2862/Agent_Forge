"""
End-to-End Self-Evolution Test & Mid-Sem Demonstration.
Demonstrates:
  Run 1 (Unverified Pipeline)
    -> Evaluate
    -> Failure Analysis (Architectural Diagnosis)
    -> Reflection Engine (5-Question Synthesis)
    -> Architecture Modifier (Mutation & Safety Validation)
  Run 2 (Evolved Verified Pipeline)
    -> Re-Evaluate
    -> Calculated Improvement Delta (Score_2 - Score_1 > 0)
"""

import pytest
from app.evaluation.evaluator import Evaluator
from app.evaluation.failure_analyzer import FailureAnalyzer
from app.reflection.reflection_engine import ReflectionEngine
from app.reflection.architecture_modifier import ArchitectureModifier
from app.schemas.reflection import IssueCategory
from tests.fixtures.mock_scenarios import (
    get_research_task_spec,
    get_run1_architecture,
    get_run1_execution_result,
    get_run2_execution_result,
)


def run_evolution_pipeline():
    """
    Executes the complete Member 3 autonomous evolution cycle.
    Returns: dictionary of artifacts, metrics, and calculated improvement delta.
    """
    evaluator = Evaluator()
    failure_analyzer = FailureAnalyzer()
    reflection_engine = ReflectionEngine(failure_analyzer=failure_analyzer)
    architecture_modifier = ArchitectureModifier()

    # =========================================================================
    # STAGE 1: RUN 1 — BASE ARCHITECTURE EVALUATION
    # =========================================================================
    task_spec = get_research_task_spec()
    arch_run1 = get_run1_architecture()
    exec_run1 = get_run1_execution_result()

    eval_result_run1 = evaluator.evaluate(
        task=task_spec,
        architecture=arch_run1,
        execution=exec_run1,
    )
    score_run1 = eval_result_run1.overall_score or eval_result_run1.metrics.task_success

    # =========================================================================
    # STAGE 2: FAILURE ANALYSIS & ARCHITECTURAL ROOT CAUSE DIAGNOSIS
    # =========================================================================
    diagnosed_issues = failure_analyzer.diagnose(
        task_spec=task_spec,
        architecture=arch_run1,
        execution_result=exec_run1,
        evaluation_result=eval_result_run1,
    )

    # =========================================================================
    # STAGE 3: REFLECTION ENGINE & RECOMMENDATION GENERATION
    # =========================================================================
    reflection_run1 = reflection_engine.reflect(
        evaluation_result=eval_result_run1,
        architecture=arch_run1,
        task=task_spec,
        execution=exec_run1,
        diagnosed_issues=diagnosed_issues,
    )

    # =========================================================================
    # STAGE 4: ARCHITECTURE MUTATION & GRAPH VALIDATION
    # =========================================================================
    arch_run2 = architecture_modifier.mutate_architecture(
        base_architecture=arch_run1,
        reflection=reflection_run1,
    )

    # =========================================================================
    # STAGE 5: RUN 2 — EVOLVED ARCHITECTURE EXECUTION & EVALUATION
    # =========================================================================
    exec_run2 = get_run2_execution_result()

    eval_result_run2 = evaluator.evaluate(
        task=task_spec,
        architecture=arch_run2,
        execution=exec_run2,
    )
    score_run2 = eval_result_run2.overall_score or eval_result_run2.metrics.task_success

    # =========================================================================
    # STAGE 6: CALCULATED IMPROVEMENT DELTA
    # =========================================================================
    improvement_delta = round(score_run2 - score_run1, 4)

    return {
        "task_spec": task_spec,
        "arch_run1": arch_run1,
        "eval_result_run1": eval_result_run1,
        "score_run1": score_run1,
        "diagnosed_issues": diagnosed_issues,
        "reflection_run1": reflection_run1,
        "arch_run2": arch_run2,
        "eval_result_run2": eval_result_run2,
        "score_run2": score_run2,
        "improvement_delta": improvement_delta,
    }


def test_end_to_end_evolution_pipeline():
    """Validates the full Run 1 -> Run 2 evolution pipeline mathematically and structurally."""
    results = run_evolution_pipeline()

    # 1. Verify Run 1 diagnosed missing verification
    categories = [i.category for i in results["diagnosed_issues"]]
    assert IssueCategory.INSUFFICIENT_VERIFICATION in categories
    assert results["eval_result_run1"].metrics.verification_status == "Unverified"

    # 2. Verify reflection synthesized actionable recommendation
    actions = [r.action for r in results["reflection_run1"].recommendations]
    assert "ADD_AGENT" in actions

    # 3. Verify architecture modifier inserted Fact Verification Agent
    arch_run2 = results["arch_run2"]
    assert len(arch_run2.agents) >= 3
    agent_ids = [a.agent_id for a in arch_run2.agents]
    assert "fact_verification_agent" in agent_ids

    # Check connection topology rewiring
    conn_pairs = [(c.source, c.target) for c in arch_run2.connections]
    assert ("fact_verification_agent", "writer_agent") in conn_pairs
    assert any(c.target == "fact_verification_agent" for c in arch_run2.connections)

    # 4. Verify Run 2 achieved Verified status and higher score
    eval_run2 = results["eval_result_run2"]
    assert eval_run2.metrics.verification_status == "Verified"
    assert eval_run2.metrics.accuracy >= 0.90
    assert eval_run2.metrics.quality > results["eval_result_run1"].metrics.quality

    # 5. Verify real, calculated improvement delta (no hardcoded constants)
    score_1 = results["score_run1"]
    score_2 = results["score_run2"]
    delta = results["improvement_delta"]

    assert score_2 > score_1
    assert delta > 0.15  # Meaningful multi-dimensional gain
    assert delta == round(score_2 - score_1, 4)


if __name__ == "__main__":
    print("==================================================================")
    print("  AGENT FORGE — MEMBER 3 SELF-EVOLUTION PIPELINE DEMONSTRATION   ")
    print("==================================================================")
    res = run_evolution_pipeline()

    print("\n--- [RUN 1: BASE ARCHITECTURE] ---")
    print(f"Architecture ID     : {res['arch_run1'].architecture_id}")
    print(f"Agents ({len(res['arch_run1'].agents)})            : {[a.agent_id for a in res['arch_run1'].agents]}")
    print(f"Verification Status : {res['eval_result_run1'].metrics.verification_status}")
    print(f"Task Success        : {res['eval_result_run1'].metrics.task_success:.4f}")
    print(f"Quality Score       : {res['eval_result_run1'].metrics.quality:.4f}")
    print(f"Accuracy Score      : {res['eval_result_run1'].metrics.accuracy:.4f}")
    print(f"RUN 1 OVERALL SCORE : {res['score_run1']:.4f}")

    print("\n--- [DIAGNOSIS & REFLECTION] ---")
    for iss in res["diagnosed_issues"]:
        print(f"[*] Detected Issue   : [{iss.category.value}] (Severity: {iss.severity})")
        print(f"    Description      : {iss.description}")
        print(f"    Evidence         : {iss.evidence}")

    for rec in res["reflection_run1"].recommendations:
        print(f"[>] Recommendation   : {rec.action} ({rec.details.get('role', 'N/A')})")
        print(f"    Reason           : {rec.reason}")
        print(f"    Expected Benefit : {rec.expected_benefit}")

    print("\n--- [RUN 2: EVOLVED ARCHITECTURE] ---")
    print(f"Architecture ID     : {res['arch_run2'].architecture_id}")
    print(f"Agents ({len(res['arch_run2'].agents)})            : {[a.agent_id for a in res['arch_run2'].agents]}")
    print(f"Connections ({len(res['arch_run2'].connections)})       : {[(c.source, c.target) for c in res['arch_run2'].connections]}")
    print(f"Verification Status : {res['eval_result_run2'].metrics.verification_status}")
    print(f"Task Success        : {res['eval_result_run2'].metrics.task_success:.4f}")
    print(f"Quality Score       : {res['eval_result_run2'].metrics.quality:.4f}")
    print(f"Accuracy Score      : {res['eval_result_run2'].metrics.accuracy:.4f}")
    print(f"RUN 2 OVERALL SCORE : {res['score_run2']:.4f}")

    print("\n==================================================================")
    print(f"  RUN 1 SCORE        : {res['score_run1']:.4f}")
    print(f"  RUN 2 SCORE        : {res['score_run2']:.4f}")
    print(f"  IMPROVEMENT DELTA  : +{res['improvement_delta']:.4f} ({res['improvement_delta']*100:.2f}%)")
    print("==================================================================")
