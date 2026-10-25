"""
Agent Forge — Research-Grade Integration Audit Verification Script.
Executes concrete, empirical tests covering:
1. Dynamic DAG generation & constraint rejection
2. Semantic memory retrieval & lexical TF vs embedding limits
3. Failure-driven evolution & decision policy enforcement
4. Quality scorer stress tests (repetitive, empty headings, contradictory, constraint-violating)
5. End-to-end baseline vs candidate execution & persistence
"""

import asyncio
import json
import os
import sys
import time
from typing import Dict, Any

from app.schemas.task import TaskSpec, Subtask, TaskType, ComplexityLevel, TaskConstraints
from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, Connection, TopologyType
from app.schemas.validator import ArchitectureValidator
from app.schemas.execution import ExecutionResult, ExecutionStatus
from app.schemas.evaluation import EvaluationResult, EvaluationMetrics
from app.schemas.reflection import ReflectionResult, ReflectionIssue, IssueCategory
from app.controller.architecture_generator import ArchitectureGenerator
from app.controller.meta_controller import MetaController
from app.memory.memory_retriever import MemoryRetriever
from app.memory.memory_store import MemoryStore
from app.memory.database import AsyncSessionFactory, init_db
from app.evaluation.evaluator import Evaluator
from app.evaluation.failure_analyzer import FailureAnalyzer
from app.evaluation.quality_scorer import QualityScorer
from app.evaluation.decision_policy import EvolutionDecisionPolicy
from app.reflection.reflection_engine import ReflectionEngine
from app.reflection.architecture_modifier import ArchitectureModifier
from app.agents.agent_factory import AgentFactory
from app.execution.execution_engine import ExecutionEngine
from app.tools.tool_registry import ToolRegistry
from app.tools import register_default_tools


async def verify_dag_generation() -> Dict[str, Any]:
    print("\n--- [AUDIT 2] Verifying Dynamic DAG Generation ---")
    gen = ArchitectureGenerator()
    results = {}

    # 1. Independent subtasks (Parallel)
    t_parallel = TaskSpec(
        task_id="audit_parallel_01",
        user_prompt="Analyze independent market datasets in parallel",
        task_type=TaskType.DATA_ANALYSIS,
        complexity=ComplexityLevel.MEDIUM,
        subtasks=[
            Subtask(id="worker_a", title="Analyze Dataset A", description="Process data A", required_capabilities=[]),
            Subtask(id="worker_b", title="Analyze Dataset B", description="Process data B", required_capabilities=[]),
        ]
    )
    arch_parallel = gen.generate_architecture(t_parallel)
    results["parallel_topology"] = arch_parallel.topology.value
    results["parallel_connections_count"] = len(arch_parallel.connections)

    # 2. Sequential dependent subtasks (Pipeline)
    t_pipeline = TaskSpec(
        task_id="audit_pipeline_01",
        user_prompt="Generate python sorting algorithm and compile test suite",
        task_type=TaskType.CODE_GENERATION,
        complexity=ComplexityLevel.MEDIUM,
        subtasks=[
            Subtask(id="st_spec", title="Define Interface", description="Define contract", required_capabilities=[]),
            Subtask(id="st_impl", title="Implement Code", description="Write code", required_capabilities=[]),
            Subtask(id="st_test", title="Write Unit Tests", description="Write tests", required_capabilities=[]),
        ]
    )
    arch_pipeline = gen.generate_architecture(t_pipeline)
    results["pipeline_topology"] = arch_pipeline.topology.value
    results["pipeline_connections"] = [f"{c.source}->{c.target}" for c in arch_pipeline.connections]

    # 3. Parallel branches converging on a synthesis agent (Hybrid DAG Fan-In)
    t_hybrid = TaskSpec(
        task_id="audit_hybrid_01",
        user_prompt="Perform multi-source competitor investigation and synthesize comprehensive executive dossier",
        task_type=TaskType.RESEARCH,
        complexity=ComplexityLevel.HIGH,
        subtasks=[
            Subtask(id="intel_1", title="Scrape Tech Stack", description="Gather tech details", required_capabilities=["web_search"]),
            Subtask(id="intel_2", title="Scrape Pricing", description="Gather pricing model", required_capabilities=["web_search"]),
            Subtask(id="synthesis", title="Synthesize Executive Dossier", description="Aggregate and evaluate", required_capabilities=[]),
        ]
    )
    arch_hybrid = gen.generate_architecture(t_hybrid)
    results["hybrid_topology"] = arch_hybrid.topology.value
    results["hybrid_connections"] = [f"{c.source}->{c.target}" for c in arch_hybrid.connections]

    # 4. Mandatory Verification Constraint
    t_verif = TaskSpec(
        task_id="audit_verif_01",
        user_prompt="Investigate aerospace structural integrity claims with mandatory verification",
        task_type=TaskType.RESEARCH,
        complexity=ComplexityLevel.MEDIUM,
        require_verification=True,
        subtasks=[
            Subtask(id="audit_research", title="Gather Aerodynamics", description="Collect data", required_capabilities=["web_search"]),
            Subtask(id="audit_report", title="Draft Aerodynamics Dossier", description="Draft doc", required_capabilities=[]),
        ]
    )
    arch_verif = gen.generate_architecture(t_verif)
    results["verification_in_last_prompt"] = "Mandatory Verification Stage" in arch_verif.agents[-1].system_prompt

    # 5. Hard Constraint: Max Agents enforcement
    t_max_agents = TaskSpec(
        task_id="audit_max_agents_01",
        user_prompt="Run comprehensive 4-stage pipeline with max_agents=2",
        task_type=TaskType.CODE_GENERATION,
        complexity=ComplexityLevel.HIGH,
        max_agents=2,
        subtasks=[
            Subtask(id="s1", title="Task 1", description="1", required_capabilities=[]),
            Subtask(id="s2", title="Task 2", description="2", required_capabilities=[]),
            Subtask(id="s3", title="Task 3", description="3", required_capabilities=[]),
            Subtask(id="s4", title="Task 4", description="4", required_capabilities=[]),
        ]
    )
    arch_clustered = gen.generate_architecture(t_max_agents)
    results["clustered_agent_count"] = len(arch_clustered.agents)
    results["max_agents_respected"] = len(arch_clustered.agents) <= 2

    # 6. Invalid Graph Rejection: Cycles and Self-Loops
    cycle_arch = ArchitectureSpec(
        architecture_id="arch_invalid_cycle",
        task_id="t_cycle",
        topology=TopologyType.PIPELINE,
        agents=[
            AgentConfigSchema(agent_id="a1", name="Agent 1", role="Role 1", objective="Obj", system_prompt="Sys"),
            AgentConfigSchema(agent_id="a2", name="Agent 2", role="Role 2", objective="Obj", system_prompt="Sys"),
        ],
        connections=[
            Connection(source="a1", target="a2"),
            Connection(source="a2", target="a1"),
        ]
    )
    cycle_val = ArchitectureValidator.validate(cycle_arch)
    results["cycle_rejected"] = not cycle_val.is_valid
    results["cycle_errors"] = cycle_val.error_messages

    return results


async def verify_semantic_memory() -> Dict[str, Any]:
    print("\n--- [AUDIT 3] Verifying Semantic Memory vs Lexical Limits ---")
    results = {}

    # Test query A: Cloud latency
    q_base = TaskSpec(
        task_id="q_cloud",
        user_prompt="Compare AWS Lambda versus Cloudflare Workers cold start latency and serverless execution overhead",
        task_type=TaskType.RESEARCH,
        complexity=ComplexityLevel.MEDIUM,
    )

    # Candidate 1: Paraphrase with different words (Serverless edge runtime performance)
    from app.memory.memory_schema import EvolutionMemoryRecord
    from datetime import datetime

    def make_dummy_rec(rec_id: str, prompt: str, task_type=TaskType.RESEARCH, rating=0.9):
        ts = TaskSpec(task_id=f"t_{rec_id}", user_prompt=prompt, task_type=task_type, complexity=ComplexityLevel.MEDIUM)
        arch = ArchitectureSpec(architecture_id=f"arch_{rec_id}", task_id=f"t_{rec_id}", topology=TopologyType.PIPELINE, agents=[AgentConfigSchema(agent_id="a1", name="A", role="R", objective="O", system_prompt="S")], connections=[])
        eval_r = EvaluationResult(evaluation_id=f"e_{rec_id}", task_id=f"t_{rec_id}", architecture_id=f"arch_{rec_id}", metrics=EvaluationMetrics(task_success=rating, quality=rating, completeness=rating, execution_time_seconds=1.0, agent_count=1), feedback_summary="Done")
        refl_r = ReflectionResult(reflection_id=f"r_{rec_id}", task_id=f"t_{rec_id}", architecture_id=f"arch_{rec_id}", identified_issues=[], recommendations=[], reflection_summary="Good")
        return EvolutionMemoryRecord(
            record_id=rec_id, task_spec=ts, architecture_spec=arch, evaluation_result=eval_r,
            reflection_result=refl_r, success_rating=rating, run_number=1, task_type=task_type,
            complexity=ComplexityLevel.MEDIUM, timestamp=datetime.utcnow(), execution_duration_seconds=1.0,
            agent_count=1, topology="pipeline", recommendation_summary="Serverless edge computing analysis"
        )

    # 1. Paraphrase with overlapping domain vocabulary
    rec_paraphrase = make_dummy_rec("rec_para", "Serverless edge runtime performance benchmarking AWS Lambda versus Cloudflare Workers")
    # 2. Unrelated with accidental keyword overlap (e.g. AWS pricing for databases and Lambda storage)
    rec_unrelated_overlap = make_dummy_rec("rec_unrelated", "AWS RDS relational database pricing and storage capacity limits")
    # 3. Pure semantic paraphrase with zero overlapping content words
    rec_zero_overlap_paraphrase = make_dummy_rec("rec_synonyms", "Evaluate distributed micro-functions initiation delays between major cloud service vendors")

    sim_paraphrase = MemoryRetriever.compute_semantic_similarity(q_base, rec_paraphrase)
    sim_overlap = MemoryRetriever.compute_semantic_similarity(q_base, rec_unrelated_overlap)
    sim_zero_overlap = MemoryRetriever.compute_semantic_similarity(q_base, rec_zero_overlap_paraphrase)

    results["sim_paraphrase_score"] = round(sim_paraphrase, 4)
    results["sim_keyword_overlap_unrelated"] = round(sim_overlap, 4)
    results["sim_zero_overlap_semantic_paraphrase"] = round(sim_zero_overlap, 4)
    results["is_learned_embedding"] = False
    results["representation_type"] = "Normalized Term Frequency (TF) Cosine Vector with Stopword Filtering (Lexical Vector)"

    return results


async def verify_quality_scorer() -> Dict[str, Any]:
    print("\n--- [AUDIT 5] Validating Quality Scorer Anti-Gaming & Edge Cases ---")
    scorer = QualityScorer()
    results = {}

    # Case A: Long repetitive text (800+ chars, but single sentence repeated 25 times)
    repeating_sentence = "The model evaluated the dataset accurately and produced robust outputs. "
    long_repetitive_text = repeating_sentence * 25  # ~1800 characters
    score_rep, breakdown_rep = scorer.score_output(
        long_repetitive_text,
        user_prompt="Provide a comprehensive cybersecurity analysis"
    )
    results["repetitive_long_text_score"] = score_rep
    results["repetitive_substance_score"] = breakdown_rep["usefulness"]
    results["repetitive_clarity_score"] = breakdown_rep["clarity"]

    # Case B: Headings with zero substance
    empty_headings_text = "# Executive Summary\n## Key Findings\n### Recommendations\n#### Conclusion\n"
    score_headings, breakdown_headings = scorer.score_output(
        empty_headings_text,
        user_prompt="Provide a comprehensive cybersecurity analysis"
    )
    results["empty_headings_score"] = score_headings
    results["empty_headings_substance"] = breakdown_headings["usefulness"]
    results["empty_headings_structure"] = breakdown_headings["structure"]

    # Case C: Ignored mandatory verification constraint
    unverified_text = (
        "# Market Analysis\n"
        "Revenue increased 45% year over year across all commercial enterprise segments.\n"
        "Customer retention remains above 95% without any customer churn observed."
    )
    score_unverif, breakdown_unverif = scorer.score_output(
        unverified_text,
        user_prompt="Provide verified market analysis",
        context={"require_verification": True}
    )
    results["unverified_text_constraint_score"] = breakdown_unverif["constraint_adherence"]
    results["unverified_total_score"] = score_unverif

    # Case D: Output with self-contradiction
    contradictory_text = (
        "# Clinical Assessment\n"
        "The treatment is completely safe and causes zero side effects in clinical trials.\n"
        "The treatment is extremely dangerous and induces severe multi-organ failures in clinical trials."
    )
    score_contra, breakdown_contra = scorer.score_output(
        contradictory_text,
        user_prompt="Assess clinical safety profile"
    )
    results["contradictory_consistency_score"] = breakdown_contra["consistency"]
    results["contradictory_total_score"] = score_contra

    # Case E: High-quality, structured, verified output
    high_qual_text = (
        "# Verified Aerospace Structural Audit\n\n"
        "## Executive Summary & Audit Verification Notice\n"
        "All telemetry claims were cross-referenced and verified against published wind tunnel test logs.\n\n"
        "## Quantitative Findings\n"
        "| Material Component | Max Tensile (MPa) | Fatigue Life (Cycles) |\n"
        "| :--- | :--- | :--- |\n"
        "| Titanium Ti-6Al-4V | 950 | 1,200,000 |\n"
        "| Carbon Composite | 1,420 | 850,000 |\n\n"
        "## Recommendations\n"
        "1. Implement continuous strain-gauge monitoring on wingbox junctions.\n"
        "2. Recalibrate ultrasonic sensors before flight envelope expansion."
    )
    score_high, breakdown_high = scorer.score_output(
        high_qual_text,
        user_prompt="Provide verified aerospace structural audit",
        context={"require_verification": True, "expected_output_format": "table"}
    )
    results["high_quality_total_score"] = score_high
    results["high_quality_breakdown"] = breakdown_high

    return results


async def verify_evolution_and_e2e() -> Dict[str, Any]:
    print("\n--- [AUDIT 4 & 6] Verifying Failure-Driven Evolution & End-to-End Pipeline ---")
    results = {}

    # Initialize SQLite memory database
    await init_db()

    # Create task that intentionally lacks verification initially to test failure-driven evolution
    task_spec = TaskSpec(
        task_id="e2e_audit_task_ev_01",
        user_prompt="Investigate electric vehicle battery thermal runaway claims, verify safety records, and synthesize an evidence-backed dossier.",
        task_type=TaskType.RESEARCH,
        complexity=ComplexityLevel.MEDIUM,
        required_capabilities=["web_search", "information_retrieval", "content_synthesis"],
        constraints=["Only cite verified statistics"],
        subtasks=[
            Subtask(
                id="researcher",
                title="EV Claims Retrieval",
                description="Gather published statistics and claims on electric vehicle battery safety.",
                required_capabilities=["web_search"],
            ),
            Subtask(
                id="reporter",
                title="Synthesize EV Report",
                description="Draft the summary report based on gathered claims.",
                required_capabilities=[],
            ),
        ],
    )

    # 1. Baseline Architecture Synthesis (v1)
    gen = ArchitectureGenerator()
    arch_v1 = gen.generate_architecture(task_spec)
    results["baseline_version"] = arch_v1.version
    results["baseline_agent_count"] = len(arch_v1.agents)
    results["baseline_agents"] = [a.agent_id for a in arch_v1.agents]

    # Setup execution environment
    registry = ToolRegistry()
    register_default_tools(registry)
    factory = AgentFactory(registry=registry)
    engine = ExecutionEngine(factory=factory)

    # 2. Execute Baseline (v1)
    t0 = time.time()
    exec_v1 = await engine.execute_architecture(
        architecture=arch_v1,
        input_data={"user_prompt": task_spec.user_prompt},
    )
    results["baseline_exec_status"] = exec_v1.status.value if hasattr(exec_v1.status, "value") else str(exec_v1.status)
    results["baseline_exec_time"] = round(time.time() - t0, 3)

    # 3. Evaluate Baseline (v1)
    evaluator = Evaluator()
    eval_v1 = evaluator.evaluate(task=task_spec, architecture=arch_v1, execution=exec_v1)
    results["baseline_metrics"] = {
        "accuracy": eval_v1.metrics.accuracy,
        "quality": eval_v1.metrics.quality,
        "verification_status": eval_v1.metrics.verification_status,
        "overall_score": eval_v1.overall_score,
    }

    # 4. Failure Diagnosis & Reflection
    failure_analyzer = FailureAnalyzer()
    reflection_engine = ReflectionEngine(failure_analyzer=failure_analyzer)
    reflection_v1 = reflection_engine.reflect(
        evaluation_result=eval_v1,
        architecture=arch_v1,
        task=task_spec,
        execution=exec_v1,
    )
    results["diagnosed_issues"] = [i.category.value for i in reflection_v1.identified_issues]
    results["proposed_actions"] = [r.action for r in reflection_v1.recommendations]

    # 5. Apply Evolution Mutation (v1 -> v2)
    modifier = ArchitectureModifier()
    arch_v2 = modifier.mutate_architecture(arch_v1, reflection_v1)
    results["candidate_version"] = arch_v2.version
    results["candidate_parent_id"] = arch_v2.parent_architecture_id
    results["candidate_agent_count"] = len(arch_v2.agents)
    results["candidate_agents"] = [a.agent_id for a in arch_v2.agents]

    # Pre-execution validation of candidate architecture
    v2_val = ArchitectureValidator.validate(arch_v2, task_spec=task_spec)
    results["candidate_validation_is_valid"] = v2_val.is_valid
    results["candidate_validation_errors"] = v2_val.error_messages

    # 6. Execute Candidate Architecture (v2)
    t1 = time.time()
    exec_v2 = await engine.execute_architecture(
        architecture=arch_v2,
        input_data={"user_prompt": task_spec.user_prompt},
    )
    results["candidate_exec_status"] = exec_v2.status.value if hasattr(exec_v2.status, "value") else str(exec_v2.status)
    results["candidate_exec_time"] = round(time.time() - t1, 3)

    # 7. Evaluate Candidate (v2)
    eval_v2 = evaluator.evaluate(task=task_spec, architecture=arch_v2, execution=exec_v2)
    results["candidate_metrics"] = {
        "accuracy": eval_v2.metrics.accuracy,
        "quality": eval_v2.metrics.quality,
        "verification_status": eval_v2.metrics.verification_status,
        "overall_score": eval_v2.overall_score,
    }

    # 8. Evolution Decision Policy Check
    decision = EvolutionDecisionPolicy.evaluate_evolution(
        v1_architecture=arch_v1,
        v2_architecture=arch_v2,
        v1_execution=exec_v1,
        v2_execution=exec_v2,
        v1_evaluation=eval_v1,
        v2_evaluation=eval_v2,
        task_spec=task_spec,
    )
    results["evolution_decision"] = decision.status.value
    results["evolution_decision_reason_codes"] = decision.reason_codes
    results["evolution_decision_rationale"] = decision.rationale
    results["evolution_score_delta"] = decision.score_delta

    # 9. Verify Rejection Case: What if candidate degraded score?
    # Create artificial degraded candidate evaluation
    degraded_metrics = eval_v1.metrics.model_copy(update={"quality": 0.20, "accuracy": 0.20})
    eval_degraded = eval_v1.model_copy(update={"metrics": degraded_metrics, "overall_score": 0.25})
    decision_rejected = EvolutionDecisionPolicy.evaluate_evolution(
        v1_architecture=arch_v1,
        v2_architecture=arch_v2,
        v1_execution=exec_v1,
        v2_execution=exec_v2,
        v1_evaluation=eval_v1,
        v2_evaluation=eval_degraded,
        task_spec=task_spec,
    )
    results["rejection_test_outcome"] = decision_rejected.status.value
    results["rejection_test_reason_codes"] = decision_rejected.reason_codes
    results["rejection_test_rationale"] = decision_rejected.rationale

    # 10. Persistence verification in DB
    async with AsyncSessionFactory() as session:
        store = MemoryStore(session)
        rec_count_before = len(await store.get_records_for_task(task_spec.task_id))
        
        # Save record
        from app.memory.memory_schema import EvolutionMemoryRecord
        from datetime import datetime
        rec = EvolutionMemoryRecord(
            record_id=f"rec_{task_spec.task_id}_v2",
            task_spec=task_spec,
            architecture_spec=arch_v2,
            evaluation_result=eval_v2,
            reflection_result=reflection_v1,
            success_rating=eval_v2.overall_score or 0.85,
            run_number=2,
            task_type=task_spec.task_type,
            complexity=task_spec.complexity,
            timestamp=datetime.utcnow(),
            execution_duration_seconds=results["candidate_exec_time"],
            agent_count=len(arch_v2.agents),
            topology=arch_v2.topology.value,
            recommendation_summary="Added Fact Verification Agent to satisfy verification constraint",
        )
        await store.save_record(rec)
        await session.commit()

        # Query back
        records_after = await store.get_records_for_task(task_spec.task_id)
        results["persisted_records_count"] = len(records_after)
        results["persisted_record_id"] = records_after[0].record_id if records_after else None

    return results


async def main():
    print("=================================================================")
    print("STARTING RESEARCH-GRADE INTEGRATION AUDIT EXPERIMENTS")
    print("=================================================================")

    dag_results = await verify_dag_generation()
    mem_results = await verify_semantic_memory()
    quality_results = await verify_quality_scorer()
    e2e_results = await verify_evolution_and_e2e()

    full_audit = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "dag_generation": dag_results,
        "semantic_memory": mem_results,
        "quality_scorer": quality_results,
        "evolution_and_e2e": e2e_results,
    }

    with open("docs/audit_execution_log.json", "w") as f:
        json.dump(full_audit, f, indent=2)

    print("\n[SUCCESS] Audit experiments successfully finished. Log written to docs/audit_execution_log.json")
    print(json.dumps(full_audit, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
