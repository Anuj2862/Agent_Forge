"""
Unit Tests for BaseAgent and Dynamic AgentFactory (Member 2 Phase 3).
"""

import unittest
from app.agents.base_agent import BaseAgent
from app.agents.agent_factory import AgentFactory
from app.schemas.architecture import AgentConfigSchema, ArchitectureSpec, TopologyType, Connection
from app.tools.tool_registry import ToolRegistry, tool_registry


class TestBaseAgent(unittest.TestCase):

    def setUp(self):
        self.config = AgentConfigSchema(
            agent_id="quantum_agent",
            name="Quantum Analyst",
            role="Quantum Physics Specialist",
            objective="Analyze quantum entanglement experiments",
            system_prompt="You are an expert in quantum mechanics.",
            tools=["python_tool"],
            input_keys=["experiment_data"],
            output_keys=["quantum_report"],
            constraints=["Must follow scientific rigour"],
        )

    def test_base_agent_creation_and_attributes(self):
        agent = BaseAgent(config=self.config)
        self.assertEqual(agent.agent_id, "quantum_agent")
        self.assertEqual(agent.role, "Quantum Physics Specialist")
        self.assertEqual(agent.input_keys, ["experiment_data"])
        self.assertEqual(agent.output_keys, ["quantum_report"])

    def test_base_agent_execution_with_mock_llm(self):
        def mock_llm(prompt, state, tools):
            return f"Simulated quantum analysis for prompt: {prompt[:20]}"

        agent = BaseAgent(config=self.config, llm_runner=mock_llm)
        initial_state = {
            "user_prompt": "Analyze Bell state measurements",
            "experiment_data": "CHSH inequality violation = 2.82",
        }

        res = agent.run(initial_state)

        self.assertEqual(res["agent_id"], "quantum_agent")
        self.assertEqual(res["agent_role"], "Quantum Physics Specialist")
        self.assertEqual(res["status"], "completed")
        self.assertIn("Simulated quantum analysis", res["output"])
        self.assertIn("quantum_report", res["updated_state"])
        self.assertEqual(res["updated_state"]["quantum_report"], res["output"])

    def test_base_agent_error_handling(self):
        def failing_llm(prompt, state, tools):
            raise RuntimeError("API quota exceeded")

        agent = BaseAgent(config=self.config, llm_runner=failing_llm)
        res = agent.run({"user_prompt": "Test error handling"})

        self.assertEqual(res["status"], "failed")
        self.assertIn("API quota exceeded", res["error"])
        self.assertIn("Execution failed", res["output"])


class TestAgentFactory(unittest.TestCase):

    def setUp(self):
        self.factory = AgentFactory(registry=tool_registry)

    def test_create_single_agent(self):
        config = AgentConfigSchema(
            agent_id="custom_agent_1",
            name="Data Cleaning Agent",
            role="Data Wrangler",
            objective="Clean noisy CSV data",
            system_prompt="Clean data accurately.",
            tools=["python_tool"],
        )

        agent = self.factory.create_agent(config)
        self.assertIsInstance(agent, BaseAgent)
        self.assertEqual(agent.agent_id, "custom_agent_1")
        self.assertEqual(len(agent.tools), 1)

    def test_create_agent_team_variable_counts(self):
        configs = [
            AgentConfigSchema(
                agent_id="ag_1",
                name="Planner",
                role="Strategic Planner",
                objective="Plan execution steps",
                system_prompt="Plan tasks.",
                tools=[],
            ),
            AgentConfigSchema(
                agent_id="ag_2",
                name="Worker",
                role="Execution Worker",
                objective="Execute subtasks",
                system_prompt="Execute work.",
                tools=["python_tool"],
            ),
            AgentConfigSchema(
                agent_id="ag_3",
                name="Reviewer",
                role="Quality Inspector",
                objective="Inspect results",
                system_prompt="Review output.",
                tools=["web_search"],
            ),
        ]

        team = self.factory.create_agent_team(configs)
        self.assertEqual(len(team), 3)
        self.assertIn("ag_1", team)
        self.assertIn("ag_2", team)
        self.assertIn("ag_3", team)

    def test_duplicate_agent_ids_rejected(self):
        configs = [
            AgentConfigSchema(
                agent_id="dup_agent",
                name="Agent A",
                role="Role A",
                objective="Obj A",
                system_prompt="Prompt A",
            ),
            AgentConfigSchema(
                agent_id="dup_agent",
                name="Agent B",
                role="Role B",
                objective="Obj B",
                system_prompt="Prompt B",
            ),
        ]

        with self.assertRaises(ValueError) as ctx:
            self.factory.create_agent_team(configs)
        self.assertIn("Duplicate agent_id 'dup_agent'", str(ctx.exception))

    def test_unknown_tool_fails_clearly(self):
        config = AgentConfigSchema(
            agent_id="bad_tool_agent",
            name="Bad Tool Agent",
            role="Tester",
            objective="Test bad tools",
            system_prompt="Prompt",
            tools=["non_existent_tool_xyz"],
        )

        with self.assertRaises(KeyError) as ctx:
            self.factory.create_agent(config)
        self.assertIn("non_existent_tool_xyz", str(ctx.exception))

    def test_same_factory_handles_two_different_architectures(self):
        # Architecture A: 2-Agent Sequential Pipeline (Research -> Summary)
        arch_a = ArchitectureSpec(
            architecture_id="arch_A_sequential",
            task_id="task_A",
            topology=TopologyType.PIPELINE,
            agents=[
                AgentConfigSchema(
                    agent_id="researcher",
                    name="Researcher",
                    role="Web Researcher",
                    objective="Search web",
                    system_prompt="Search topic",
                    tools=["web_search"],
                ),
                AgentConfigSchema(
                    agent_id="summarizer",
                    name="Summarizer",
                    role="Text Summarizer",
                    objective="Summarize findings",
                    system_prompt="Summarize text",
                    tools=[],
                ),
            ],
            connections=[Connection(source="researcher", target="summarizer")],
        )

        # Architecture B: 4-Agent Parallel/Hybrid Topology (Planner -> Coder/Tester/Doc -> Merger)
        arch_b = ArchitectureSpec(
            architecture_id="arch_B_hybrid",
            task_id="task_B",
            topology=TopologyType.HYBRID,
            agents=[
                AgentConfigSchema(
                    agent_id="planner",
                    name="Planner",
                    role="Software Architect",
                    objective="Design system",
                    system_prompt="Design architecture",
                    tools=[],
                ),
                AgentConfigSchema(
                    agent_id="coder",
                    name="Coder",
                    role="Python Developer",
                    objective="Write code",
                    system_prompt="Write Python code",
                    tools=["python_tool"],
                ),
                AgentConfigSchema(
                    agent_id="tester",
                    name="Tester",
                    role="QA Engineer",
                    objective="Run tests",
                    system_prompt="Verify software",
                    tools=["python_tool"],
                ),
                AgentConfigSchema(
                    agent_id="reviewer",
                    name="Reviewer",
                    role="Code Reviewer",
                    objective="Review pull request",
                    system_prompt="Review code quality",
                    tools=["document_retriever"],
                ),
            ],
            connections=[
                Connection(source="planner", target="coder"),
                Connection(source="planner", target="tester"),
                Connection(source="coder", target="reviewer"),
                Connection(source="tester", target="reviewer"),
            ],
        )

        # Factory creates team for Architecture A
        team_a = self.factory.create_from_architecture(arch_a)
        self.assertEqual(len(team_a), 2)
        self.assertEqual(set(team_a.keys()), {"researcher", "summarizer"})

        # Exact SAME factory creates team for Architecture B without code changes
        team_b = self.factory.create_from_architecture(arch_b)
        self.assertEqual(len(team_b), 4)
        self.assertEqual(set(team_b.keys()), {"planner", "coder", "tester", "reviewer"})

    def test_capability_resolution_code_execution_to_python_tool(self):
        config = AgentConfigSchema(
            agent_id="coder",
            name="Coder",
            role="Programmer",
            objective="Write code",
            system_prompt="Write code",
            tools=["code_execution"],
        )
        agent = self.factory.create_agent(config)
        self.assertEqual(len(agent.tools), 1)
        res = agent.tools[0]("result = 5 * 5")
        self.assertIn("25", str(res))

    def test_capability_resolution_information_retrieval_to_document_retriever(self):
        config = AgentConfigSchema(
            agent_id="retriever",
            name="Retriever",
            role="Researcher",
            objective="Retrieve info",
            system_prompt="Retrieve docs",
            tools=["information_retrieval"],
        )
        agent = self.factory.create_agent(config)
        self.assertEqual(len(agent.tools), 1)
        res = agent.tools[0]("test query")
        self.assertIn("documents", str(res).lower())

    def test_capability_resolution_web_search_remains_web_search(self):
        config = AgentConfigSchema(
            agent_id="searcher",
            name="Searcher",
            role="Web Searcher",
            objective="Search web",
            system_prompt="Search web",
            tools=["web_search"],
        )
        agent = self.factory.create_agent(config)
        self.assertEqual(len(agent.tools), 1)
        res = agent.tools[0]("artificial intelligence")
        self.assertIn("artificial intelligence", str(res))

    def test_non_executable_capability_data_analysis_no_key_error(self):
        config = AgentConfigSchema(
            agent_id="analyst",
            name="Analyst",
            role="Data Analyst",
            objective="Analyze data",
            system_prompt="Analyze patterns",
            tools=["data_analysis"],
        )
        agent = self.factory.create_agent(config)
        self.assertIsNotNone(agent)
        self.assertEqual(len(agent.tools), 0)

    def test_non_executable_capability_table_generation_no_key_error(self):
        config = AgentConfigSchema(
            agent_id="formatter",
            name="Formatter",
            role="Table Generator",
            objective="Format tables",
            system_prompt="Format data into markdown tables",
            tools=["table_generation", "data_loading"],
        )
        agent = self.factory.create_agent(config)
        self.assertIsNotNone(agent)
        self.assertEqual(len(agent.tools), 0)

    def test_existing_direct_tool_names_still_work(self):
        config = AgentConfigSchema(
            agent_id="multi_tool",
            name="Multi Tool Agent",
            role="Engineer",
            objective="Multi-step work",
            system_prompt="Use tools",
            tools=["web_search", "python_tool", "document_retriever"],
        )
        agent = self.factory.create_agent(config)
        self.assertEqual(len(agent.tools), 3)


if __name__ == "__main__":
    unittest.main()
