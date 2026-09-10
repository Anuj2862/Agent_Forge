"""
Realistic Mock Execution Fixtures and Scenarios for Member 3 Testing & Demonstration.
Simulates realistic multi-agent execution results without depending on Member 2's runtime.
"""

from app.schemas.task import TaskSpec, TaskType, ComplexityLevel, Subtask
from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, TopologyType, Connection
from app.schemas.execution import ExecutionResult, AgentExecutionTrace, ExecutionStatus, ToolCallRecord


def get_research_task_spec() -> TaskSpec:
    """Returns a realistic enterprise research task requiring factual verification."""
    return TaskSpec(
        task_id="task_cyber_001",
        user_prompt="Research the impact of Generative AI on enterprise cybersecurity, verify key threat vectors, and produce a verified markdown report.",
        task_type=TaskType.RESEARCH,
        complexity=ComplexityLevel.MEDIUM,
        subtasks=[
            Subtask(
                id="subtask_1",
                title="Information Gathering",
                description="Collect recent data and case studies on Generative AI cybersecurity risks.",
                required_capabilities=["research", "web_search"],
            ),
            Subtask(
                id="subtask_2",
                title="Factual Verification",
                description="Cross-reference claims and verify documented vulnerabilities against CVE databases.",
                required_capabilities=["verification", "accuracy_checking"],
            ),
            Subtask(
                id="subtask_3",
                title="Executive Report Writing",
                description="Synthesize verified findings into a structured markdown report with key recommendations.",
                required_capabilities=["writing", "synthesis"],
            ),
        ],
        required_capabilities=["research", "web_search", "verification", "writing"],
        constraints=["Ensure factual accuracy and verify claims before reporting"],
        expected_output_format="verified_markdown_report",
    )


def get_run1_architecture() -> ArchitectureSpec:
    """
    Synthesizes Run 1 Architecture (VULNERABLE):
    Pipeline: Research Agent -> Writer Agent.
    Deficiency: Missing independent verification stage!
    """
    research_agent = AgentConfigSchema(
        agent_id="research_agent",
        name="Cybersecurity Research Agent",
        role="Information Researcher",
        objective="Gather threat intelligence on GenAI cybersecurity risks.",
        system_prompt="You are a research agent. Gather information on GenAI risks.",
        tools=["web_search"],
        input_keys=["task_prompt"],
        output_keys=["raw_research"],
        constraints=[],
    )
    writer_agent = AgentConfigSchema(
        agent_id="writer_agent",
        name="Executive Report Writer",
        role="Report Writer",
        objective="Synthesize gathered findings into an executive report.",
        system_prompt="You are a technical writer. Synthesize the findings into an executive report.",
        tools=[],
        input_keys=["raw_research"],
        output_keys=["final_report"],
        constraints=[],
    )
    return ArchitectureSpec(
        architecture_id="arch_run1_pipeline",
        task_id="task_cyber_001",
        topology=TopologyType.PIPELINE,
        agents=[research_agent, writer_agent],
        connections=[Connection(source="research_agent", target="writer_agent")],
        meta_reasoning="Synthesized 2-agent pipeline connecting research directly to writer.",
    )


def get_run1_execution_result() -> ExecutionResult:
    """
    Realistic execution result for Run 1 (Research -> Writer).
    Output contains unverified claims and no verification evidence.
    """
    report_text = """# Executive Report: Generative AI in Enterprise Cybersecurity

## 1. Threat Landscape Overview
Generative AI poses novel security challenges for modern enterprises. Attackers utilize automated LLMs to scale social engineering.

## 2. Unverified Threat Vectors
- Deepfake voice phishing has bypassed 98% of biometric authentication systems globally.
- Autonomous zero-day exploitation scripts are currently weaponized by common threat actors.

## 3. Recommendations
- Implement continuous employee training.
- Update perimeter defenses.
"""
    return ExecutionResult(
        execution_id="exec_run1_001",
        task_id="task_cyber_001",
        architecture_id="arch_run1_pipeline",
        status=ExecutionStatus.SUCCESS,
        final_output=report_text,
        step_outputs={
            "research_agent": {"raw_research": "GenAI enables automated phishing and potential zero-day synthesis."},
            "writer_agent": {"final_report": report_text},
        },
        agent_traces=[
            AgentExecutionTrace(
                agent_id="research_agent",
                agent_name="Cybersecurity Research Agent",
                role="Information Researcher",
                status=ExecutionStatus.SUCCESS,
                input_data={"prompt": "GenAI cybersecurity risks"},
                output_data={"raw_research": "GenAI enables automated phishing."},
                tool_calls=[
                    ToolCallRecord(tool_name="web_search", success=True, duration_seconds=1.2)
                ],
                duration_seconds=3.5,
                unverified_claims=["98% biometric bypass claim not corroborated"],
            ),
            AgentExecutionTrace(
                agent_id="writer_agent",
                agent_name="Executive Report Writer",
                role="Report Writer",
                status=ExecutionStatus.SUCCESS,
                input_data={"raw_research": "GenAI enables automated phishing."},
                output_data={"final_report": report_text},
                tool_calls=[],
                duration_seconds=2.8,
            ),
        ],
        total_execution_time=6.3,
        iteration_count=1,
        total_tool_calls=1,
        errors=[],
        metadata={"model": "gemini-1.5-pro", "temperature": 0.2},
    )


def get_run2_execution_result() -> ExecutionResult:
    """
    Realistic execution result for Run 2 (Research -> Fact Verification -> Writer).
    Output passes verification with corroborated claims and verified citations.
    """
    verified_report_text = """# Verified Executive Report: Generative AI in Enterprise Cybersecurity

## 1. Executive Summary & Verification Notice
**Verification Status**: All statements corroborated by Fact Verification Agent against enterprise telemetry and CVE databases.

## 2. Corroborated Threat Vectors
- **Automated Phishing**: High-frequency spear-phishing campaigns show a 40% increase in click-through rates when LLM-generated.
- **Prompt Injection & Data Leakage**: Insecure internal LLM integrations expose proprietary source code through indirect prompt injection.
- **Deepfake Impersonation**: Social engineering via synthetic voice is an emerging enterprise risk, requiring multi-factor out-of-band validation.

## 3. Strategic Mitigation Plan
- Establish rigid content inspection and data loss prevention (DLP) across internal AI gateways.
- Mandate multi-channel authorization protocols for financial wire and credential operations.
- Maintain human-in-the-loop validation for automated code deployment workflows.
"""
    return ExecutionResult(
        execution_id="exec_run2_002",
        task_id="task_cyber_001",
        architecture_id="arch_run1_pipeline_v2",
        status=ExecutionStatus.SUCCESS,
        final_output=verified_report_text,
        step_outputs={
            "research_agent": {"raw_research": "GenAI threats include spear phishing, prompt injection, and audio deepfakes."},
            "fact_verification_agent": {
                "verified_findings": "Confirmed 40% spear phishing rise; validated prompt injection CVE risk vectors.",
                "verification_status": "passed",
                "verified": True,
            },
            "writer_agent": {"final_report": verified_report_text},
        },
        agent_traces=[
            AgentExecutionTrace(
                agent_id="research_agent",
                agent_name="Cybersecurity Research Agent",
                role="Information Researcher",
                status=ExecutionStatus.SUCCESS,
                input_data={"prompt": "GenAI cybersecurity risks"},
                output_data={"raw_research": "Raw findings gathered."},
                tool_calls=[ToolCallRecord(tool_name="web_search", success=True, duration_seconds=1.1)],
                duration_seconds=3.2,
            ),
            AgentExecutionTrace(
                agent_id="fact_verification_agent",
                agent_name="Fact Verification Agent",
                role="Factual Verification Specialist",
                status=ExecutionStatus.SUCCESS,
                input_data={"raw_research": "Raw findings gathered."},
                output_data={"verified_findings": "All core claims verified against databases.", "verified": True},
                tool_calls=[ToolCallRecord(tool_name="web_search", success=True, duration_seconds=1.4)],
                duration_seconds=3.8,
                verified_claims=[
                    "Spear-phishing click-through increase corroborated",
                    "Prompt injection data leakage vectors validated",
                    "Voice deepfake social engineering risk confirmed",
                ],
                unverified_claims=[],
                contradictions_found=[],
            ),
            AgentExecutionTrace(
                agent_id="writer_agent",
                agent_name="Executive Report Writer",
                role="Report Writer",
                status=ExecutionStatus.SUCCESS,
                input_data={"verified_findings": "All core claims verified."},
                output_data={"final_report": verified_report_text},
                tool_calls=[],
                duration_seconds=3.1,
            ),
        ],
        total_execution_time=10.1,
        iteration_count=1,
        total_tool_calls=2,
        errors=[],
        metadata={"model": "gemini-1.5-pro", "run": 2},
    )


def get_failed_execution_result() -> ExecutionResult:
    """Simulates a broken/failing execution trace with errors and empty output."""
    return ExecutionResult(
        execution_id="exec_failed_001",
        task_id="task_cyber_001",
        architecture_id="arch_run1_pipeline",
        status=ExecutionStatus.FAILED,
        final_output="",
        step_outputs={},
        agent_traces=[
            AgentExecutionTrace(
                agent_id="research_agent",
                status=ExecutionStatus.FAILED,
                duration_seconds=0.5,
                error_message="ConnectionError: Failed to reach external search API",
            )
        ],
        total_execution_time=0.5,
        iteration_count=1,
        total_tool_calls=0,
        errors=["ConnectionError: Failed to reach external search API"],
    )
