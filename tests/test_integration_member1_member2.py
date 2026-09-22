"""
End-to-End Integration Tests: Member 1 (ArchitectureGenerator) -> Member 2 (AgentFactory & ExecutionEngine).

Proves that an ArchitectureSpec produced by Member 1's ArchitectureGenerator can be consumed
by Member 2's AgentFactory and executed by Member 2's real LangGraph ExecutionEngine.
"""

import unittest
from app.controller.architecture_generator import ArchitectureGenerator
from app.schemas.task import TaskSpec, Subtask, TaskType, ComplexityLevel
from app.schemas.architecture import ArchitectureSpec, TopologyType
from app.schemas.execution import ExecutionStatus, ExecutionResult
from app.agents.agent_factory import AgentFactory
from app.execution.execution_engine import ExecutionEngine
from app.tools.tool_registry import ToolRegistry
from app.tools import register_default_tools


class TestMember1ToMember2Integration(unittest.TestCase):
    """Integration test suite proving Member 1 ArchitectureSpec -> Member 2 Engine pipeline."""

    def setUp(self):
        self.generator = ArchitectureGenerator()
        # Use isolated tool registry initialized with standard default tools
        self.isolated_registry = ToolRegistry()
        register_default_tools(self.isolated_registry)
        self.factory = AgentFactory(registry=self.isolated_registry)
        self.engine = ExecutionEngine(factory=self.factory)

    def tearDown(self):
        self.isolated_registry.clear()

    def test_member1_pipeline_to_member2_execution(self):
        """
        TEST 1 — MEMBER 1 PIPELINE -> MEMBER 2
        Uses the actual Member 1 ArchitectureGenerator to synthesize a sequential pipeline.
        Passes the spec to AgentFactory and runs it through real LangGraph ExecutionEngine.
        """
        task_spec = TaskSpec(
            task_id="integration_task_pipe_001",
            user_prompt="Build a verified Python data processing script.",
            task_type=TaskType.CODE_GENERATION,
            complexity=ComplexityLevel.MEDIUM,
            subtasks=[
                Subtask(
                    id="plan_stage",
                    title="Design Solution",
                    description="Formulate the architecture plan for the script.",
                    required_capabilities=["information_retrieval"],
                ),
                Subtask(
                    id="code_stage",
                    title="Implement Script",
                    description="Write the Python implementation.",
                    required_capabilities=["code_execution"],
                ),
                Subtask(
                    id="review_stage",
                    title="Review and Analyze",
                    description="Verify correctness and analyze output tables.",
                    required_capabilities=["data_analysis", "table_generation"],
                ),
            ],
            required_capabilities=["information_retrieval", "code_execution", "data_analysis"],
            constraints=["Ensure modular structure", "No third-party web calls"],
            expected_output_format="code_and_report",
        )

        # 1. Synthesize ArchitectureSpec using actual Member 1 ArchitectureGenerator
        arch_spec = self.generator.generate_architecture(task_spec)

        # 2. Assert valid ArchitectureSpec from Member 1
        self.assertIsInstance(arch_spec, ArchitectureSpec)
        self.assertEqual(arch_spec.task_id, "integration_task_pipe_001")
        self.assertEqual(arch_spec.topology, TopologyType.PIPELINE)
        self.assertEqual(len(arch_spec.agents), 3)
        self.assertEqual(len(arch_spec.connections), 2)
        # Verify Member 1 naming conventions and properties
        self.assertEqual(arch_spec.agents[0].name, "Design Solution Agent")
        self.assertEqual(arch_spec.agents[1].name, "Implement Script Agent")
        self.assertEqual(arch_spec.agents[2].name, "Review And Analyze Agent")
        self.assertIn("The task is classified as code_generation", arch_spec.meta_reasoning)

        # 3. Create agents with Member 2 AgentFactory
        agents = self.factory.create_from_architecture(arch_spec)
        self.assertEqual(len(agents), 3)
        # Verify capability resolution:
        # plan_stage has information_retrieval -> document_retriever tool
        self.assertEqual(len(agents["plan_stage"].tools), 1)
        # code_stage has code_execution -> python_tool
        self.assertEqual(len(agents["code_stage"].tools), 1)
        # review_stage has data_analysis and table_generation (non-executable capabilities, no crash)
        self.assertEqual(len(agents["review_stage"].tools), 0)

        # 4. Mock runner for deterministic LLM responses and upstream propagation tracking
        execution_order = []

        def mock_llm_runner(prompt, state, tools):
            current = state.get("current_agent")
            execution_order.append(current)
            return f"Synthesized output from {current}"

        # 5. Execute using real LangGraph ExecutionEngine
        result = self.engine.run_architecture(
            architecture=arch_spec,
            input_data={"user_prompt": task_spec.user_prompt},
            agents=agents,
            llm_runner=mock_llm_runner,
        )

        # 6. Comprehensive assertions
        self.assertIsInstance(result, ExecutionResult)
        self.assertEqual(result.status, ExecutionStatus.SUCCESS)
        self.assertIsNone(result.error)
        self.assertEqual(result.architecture_id, arch_spec.architecture_id)
        self.assertEqual(result.task_id, task_spec.task_id)
        self.assertEqual(result.agent_count, 3)
        self.assertEqual(result.total_steps, 3)
        self.assertEqual(len(result.step_history), 3)
        self.assertEqual(execution_order, ["plan_stage", "code_stage", "review_stage"])
        self.assertIn("Synthesized output from review_stage", result.final_output)

    def test_member1_parallel_to_member2_execution(self):
        """
        TEST 2 — MEMBER 1 PARALLEL -> MEMBER 2
        Uses Member 1's ArchitectureGenerator to synthesize a parallel multi-agent architecture.
        Passes the spec to AgentFactory and runs it through real LangGraph ExecutionEngine.
        Verifies all parallel branches run independently with empty connections.
        """
        task_spec = TaskSpec(
            task_id="integration_task_parallel_002",
            user_prompt="Conduct independent multi-domain research.",
            task_type=TaskType.RESEARCH,
            complexity=ComplexityLevel.HIGH,
            subtasks=[
                Subtask(
                    id="ai_research",
                    title="AI Safety Research",
                    description="Investigate alignment and governance.",
                    required_capabilities=["web_search"],
                ),
                Subtask(
                    id="econ_research",
                    title="Economic Impact Analysis",
                    description="Analyze economic disruption metrics.",
                    required_capabilities=["data_analysis", "table_generation"],
                ),
                Subtask(
                    id="infra_research",
                    title="Compute Infrastructure Assessment",
                    description="Assess datacenters and hardware.",
                    required_capabilities=["information_retrieval"],
                ),
            ],
            required_capabilities=["web_search", "data_analysis", "information_retrieval"],
            constraints=["Produce separate section findings"],
            expected_output_format="comprehensive_report",
        )

        # 1. Synthesize ArchitectureSpec using actual Member 1 ArchitectureGenerator
        arch_spec = self.generator.generate_architecture(task_spec)

        # 2. Assert valid ArchitectureSpec with PARALLEL topology and connections=[]
        self.assertIsInstance(arch_spec, ArchitectureSpec)
        self.assertEqual(arch_spec.task_id, "integration_task_parallel_002")
        self.assertEqual(arch_spec.topology, TopologyType.PARALLEL)
        self.assertEqual(len(arch_spec.agents), 3)
        # Member 1 intentionally produces empty connections for parallel
        self.assertEqual(arch_spec.connections, [])
        self.assertIn("parallel multi-agent topology was selected", arch_spec.meta_reasoning)

        # 3. Create agents with Member 2 AgentFactory
        agents = self.factory.create_from_architecture(arch_spec)
        self.assertEqual(len(agents), 3)
        self.assertEqual(set(agents.keys()), {"ai_research", "econ_research", "infra_research"})

        # 4. Mock runner tracking prompts seen by each parallel branch
        prompts_by_agent = {}

        def mock_llm_runner(prompt, state, tools):
            current = state.get("current_agent")
            prompts_by_agent[current] = prompt
            return f"Findings from {current}"

        # 5. Execute using real LangGraph ExecutionEngine
        result = self.engine.run_architecture(
            architecture=arch_spec,
            input_data={"user_prompt": task_spec.user_prompt},
            agents=agents,
            llm_runner=mock_llm_runner,
        )

        # 6. Assertions
        self.assertIsInstance(result, ExecutionResult)
        self.assertEqual(result.status, ExecutionStatus.SUCCESS)
        self.assertIsNone(result.error)
        self.assertEqual(result.architecture_id, arch_spec.architecture_id)
        self.assertEqual(result.task_id, task_spec.task_id)

        # ALL generated agents executed
        self.assertEqual(result.agent_count, 3)
        self.assertEqual(result.total_steps, 3)
        executed_agent_ids = {step.agent_id for step in result.step_history}
        self.assertEqual(executed_agent_ids, {"ai_research", "econ_research", "infra_research"})

        # Final output aggregates all parallel branch outputs
        for aid in ["ai_research", "econ_research", "infra_research"]:
            self.assertIn(f"[{aid} Output]: Findings from {aid}", result.final_output)

        # Non-sequential execution verification: no branch received output from any other branch
        for aid, prompt_content in prompts_by_agent.items():
            self.assertIn("Conduct independent multi-domain research", prompt_content)
            for other_aid in ["ai_research", "econ_research", "infra_research"]:
                if other_aid != aid:
                    self.assertNotIn(f"Findings from {other_aid}", prompt_content)


if __name__ == "__main__":
    unittest.main()
