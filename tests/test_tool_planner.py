"""
Unit Tests for ToolPlanner (Member 2 Tool Planning Subsystem).
"""

import unittest
from app.agents.base_agent import BaseAgent
from app.agents.agent_factory import AgentFactory
from app.agents.tool_planner import (
    ToolPlanner,
    ToolResolutionError,
    CAPABILITY_TO_TOOL,
    NON_EXECUTABLE_CAPABILITIES,
)
from app.schemas.architecture import (
    AgentConfigSchema,
    ArchitectureSpec,
    TopologyType,
    Connection,
)
from app.tools.tool_registry import ToolRegistry, tool_registry


class TestToolPlanner(unittest.TestCase):

    def setUp(self):
        self.registry = tool_registry
        self.planner = ToolPlanner(registry=self.registry)

    def test_direct_registered_tool_resolution(self):
        """1. Direct registered tool names resolve correctly."""
        resolved = self.planner.resolve_tool_names(["web_search"])
        self.assertEqual(resolved, ["web_search"])

    def test_capability_to_tool_resolution(self):
        """2. Capability strings map to the expected registered tool names."""
        resolved = self.planner.resolve_tool_names(["code_execution"])
        self.assertEqual(resolved, ["python_tool"])

        resolved_retrieval = self.planner.resolve_tool_names(["information_retrieval"])
        self.assertEqual(resolved_retrieval, ["document_retriever"])

    def test_python_tool_capability(self):
        """3. python_tool as both direct name and capability maps cleanly."""
        resolved_direct = self.planner.resolve_tool_names(["python_tool"])
        self.assertEqual(resolved_direct, ["python_tool"])

        resolved_mapped = self.planner.resolve_tool_names(["code_execution"])
        self.assertEqual(resolved_mapped, ["python_tool"])

    def test_document_retriever_capability(self):
        """4. document_retriever as direct name and capability maps cleanly."""
        resolved_direct = self.planner.resolve_tool_names(["document_retriever"])
        self.assertEqual(resolved_direct, ["document_retriever"])

        resolved_mapped = self.planner.resolve_tool_names(["information_retrieval"])
        self.assertEqual(resolved_mapped, ["document_retriever"])

    def test_multiple_tools_resolution(self):
        """5. Multiple distinct tools resolve correctly in the specified order."""
        requirements = ["web_search", "code_execution", "document_retriever"]
        resolved = self.planner.resolve_tool_names(requirements)
        self.assertEqual(resolved, ["web_search", "python_tool", "document_retriever"])

    def test_duplicate_removal_preserving_order(self):
        """6. Duplicates (even via alias/capability) are deduplicated while preserving order."""
        requirements = [
            "web_search",
            "code_execution",
            "python_tool",  # duplicate of code_execution -> python_tool
            "web_search",   # direct duplicate
            "information_retrieval",
            "document_retriever",  # duplicate of information_retrieval
        ]
        resolved = self.planner.resolve_tool_names(requirements)
        self.assertEqual(resolved, ["web_search", "python_tool", "document_retriever"])

    def test_non_executable_capabilities_ignored_without_error(self):
        """7. Analytical non-executable capabilities do not raise errors and are skipped."""
        requirements = [
            "data_analysis",
            "web_search",
            "data_loading",
            "table_generation",
        ]
        resolved = self.planner.resolve_tool_names(requirements)
        self.assertEqual(resolved, ["web_search"])

    def test_all_non_executable_capabilities_returns_empty(self):
        """Non-executable capabilities alone yield an empty tool list without raising."""
        requirements = ["data_analysis", "data_loading", "table_generation"]
        resolved = self.planner.resolve_tool_names(requirements)
        self.assertEqual(resolved, [])

    def test_unknown_executable_capability_raises_tool_resolution_error(self):
        """8. Unknown executable tool or capability raises ToolResolutionError (subclass of ValueError)."""
        with self.assertRaises(ToolResolutionError) as ctx:
            self.planner.resolve_tool_names(["quantum_simulator_tool_999"])
        self.assertIn("quantum_simulator_tool_999", str(ctx.exception))
        # Ensure it subclasses ValueError and KeyError
        self.assertIsInstance(ctx.exception, ValueError)
        self.assertIsInstance(ctx.exception, KeyError)

    def test_plan_architecture_produces_structured_assignments(self):
        """Test plan() called on ArchitectureSpec produces structured agent_id -> tool list."""
        arch = ArchitectureSpec(
            architecture_id="arch_test_plan",
            task_id="task_test",
            topology=TopologyType.PIPELINE,
            agents=[
                AgentConfigSchema(
                    agent_id="agent_1",
                    name="Researcher",
                    role="Research Specialist",
                    objective="Gather intel",
                    system_prompt="Research carefully",
                    tools=["web_search", "information_retrieval"],
                ),
                AgentConfigSchema(
                    agent_id="agent_2",
                    name="Analyst",
                    role="Data Analyst",
                    objective="Analyze findings",
                    system_prompt="Analyze carefully",
                    tools=["data_analysis", "code_execution", "python_tool"],
                ),
                AgentConfigSchema(
                    agent_id="agent_3",
                    name="Writer",
                    role="Report Writer",
                    objective="Write report",
                    system_prompt="Draft output",
                    tools=["table_generation"],
                ),
            ],
            connections=[
                Connection(source="agent_1", target="agent_2"),
                Connection(source="agent_2", target="agent_3"),
            ],
        )

        assignments = self.planner.plan(arch)

        self.assertIsInstance(assignments, dict)
        self.assertEqual(len(assignments), 3)
        self.assertEqual(assignments["agent_1"], ["web_search", "document_retriever"])
        self.assertEqual(assignments["agent_2"], ["python_tool"])  # deduplicated
        self.assertEqual(assignments["agent_3"], [])  # table_generation is non-executable

    def test_agent_factory_integration_with_tool_planner(self):
        """9. AgentFactory uses ToolPlanner to resolve tools for BaseAgent instances."""
        factory = AgentFactory(registry=self.registry, planner=self.planner)
        arch = ArchitectureSpec(
            architecture_id="arch_factory_int",
            task_id="task_factory",
            topology=TopologyType.PIPELINE,
            agents=[
                AgentConfigSchema(
                    agent_id="researcher",
                    name="Researcher",
                    role="Search Agent",
                    objective="Search queries",
                    system_prompt="Search web",
                    tools=["web_search", "information_retrieval"],
                ),
                AgentConfigSchema(
                    agent_id="coder",
                    name="Coder",
                    role="Programmer",
                    objective="Run scripts",
                    system_prompt="Code runner",
                    tools=["code_execution", "data_analysis"],
                ),
            ],
            connections=[Connection(source="researcher", target="coder")],
        )

        team = factory.create_from_architecture(arch)

        self.assertIn("researcher", team)
        self.assertIn("coder", team)

        # Researcher should have web_search and document_retriever callables
        researcher = team["researcher"]
        self.assertEqual(len(researcher.tools), 2)
        # Coder should have python_tool callable (data_analysis ignored)
        coder = team["coder"]
        self.assertEqual(len(coder.tools), 1)

        # Verify callables are functional
        code_res = coder.tools[0]("result = 10 * 10")
        self.assertIn("100", str(code_res))

    def test_agent_factory_single_agent_creation_with_planner(self):
        """AgentFactory.create_agent resolves capabilities via ToolPlanner."""
        factory = AgentFactory(registry=self.registry)
        config = AgentConfigSchema(
            agent_id="worker",
            name="Worker",
            role="Task Worker",
            objective="Do work",
            system_prompt="Work prompt",
            tools=["code_execution", "python_tool"],
        )
        agent = factory.create_agent(config)
        self.assertEqual(len(agent.tools), 1)

    def test_tool_planner_invalid_argument(self):
        """Passing an invalid object to plan() raises ValueError."""
        with self.assertRaises(ValueError):
            self.planner.plan("invalid_argument_type")


if __name__ == "__main__":
    unittest.main()
