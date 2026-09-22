"""
Unit Tests for Dynamic Execution Engine (Member 2 Phase 4).
Tests Pipeline & Parallel topologies, retries, failure handling, and multi-architecture demo.
"""

import unittest
from app.execution.execution_engine import ExecutionEngine
from app.execution.pipeline_executor import PipelineExecutor
from app.execution.parallel_executor import ParallelExecutor
from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, TopologyType, Connection
from app.schemas.execution import ExecutionStatus


class TestExecutionEngine(unittest.TestCase):

    def setUp(self):
        self.engine = ExecutionEngine()

    def test_1_simple_two_agent_pipeline(self):
        arch = ArchitectureSpec(
            architecture_id="arch_2_agent_pipeline",
            task_id="task_001",
            topology=TopologyType.PIPELINE,
            agents=[
                AgentConfigSchema(
                    agent_id="agent_a",
                    name="Researcher",
                    role="Information Researcher",
                    objective="Research topic",
                    system_prompt="Research info",
                    tools=["web_search"],
                ),
                AgentConfigSchema(
                    agent_id="agent_b",
                    name="Writer",
                    role="Report Writer",
                    objective="Draft report",
                    system_prompt="Write draft",
                    tools=[],
                ),
            ],
            connections=[Connection(source="agent_a", target="agent_b")],
        )

        outputs_logged = []

        def mock_llm(prompt, state, tools):
            current = state.get("current_agent")
            outputs_logged.append((current, prompt))
            return f"Output from {current}"

        result = self.engine.run_architecture(arch, {"user_prompt": "Research AI"}, llm_runner=mock_llm)

        self.assertEqual(result.status, ExecutionStatus.SUCCESS)
        self.assertEqual(result.total_steps, 2)
        self.assertEqual(len(result.step_history), 2)
        self.assertEqual(result.step_history[0].agent_id, "agent_a")
        self.assertEqual(result.step_history[1].agent_id, "agent_b")

        # Verify B received A's output in prompt context
        b_prompt = outputs_logged[1][1]
        self.assertIn("[agent_a Output]: Output from agent_a", b_prompt)
        self.assertEqual(result.final_output, "Output from agent_b")

    def test_2_four_agent_pipeline(self):
        arch = ArchitectureSpec(
            architecture_id="arch_4_agent_pipeline",
            task_id="task_002",
            topology=TopologyType.PIPELINE,
            agents=[
                AgentConfigSchema(agent_id="a1", name="A1", role="Role A1", objective="Obj A1", system_prompt="P A1"),
                AgentConfigSchema(agent_id="a2", name="A2", role="Role A2", objective="Obj A2", system_prompt="P A2"),
                AgentConfigSchema(agent_id="a3", name="A3", role="Role A3", objective="Obj A3", system_prompt="P A3"),
                AgentConfigSchema(agent_id="a4", name="A4", role="Role A4", objective="Obj A4", system_prompt="P A4"),
            ],
            connections=[
                Connection(source="a1", target="a2"),
                Connection(source="a2", target="a3"),
                Connection(source="a3", target="a4"),
            ],
        )

        def mock_llm(prompt, state, tools):
            return f"Result_{state.get('current_agent')}"

        result = self.engine.run_architecture(arch, {"user_prompt": "Pipeline task"}, llm_runner=mock_llm)

        self.assertEqual(result.status, ExecutionStatus.SUCCESS)
        self.assertEqual(result.total_steps, 4)
        step_agent_ids = [step.agent_id for step in result.step_history]
        self.assertEqual(step_agent_ids, ["a1", "a2", "a3", "a4"])
        self.assertEqual(result.final_output, "Result_a4")

    def test_3_parallel_architecture(self):
        # Topology: A -> B, A -> C, B -> D, C -> D
        arch = ArchitectureSpec(
            architecture_id="arch_parallel_dag",
            task_id="task_003",
            topology=TopologyType.PARALLEL,
            agents=[
                AgentConfigSchema(agent_id="node_a", name="Root", role="Root Planner", objective="Obj", system_prompt="P"),
                AgentConfigSchema(agent_id="node_b", name="Branch B", role="Data B", objective="Obj", system_prompt="P"),
                AgentConfigSchema(agent_id="node_c", name="Branch C", role="Data C", objective="Obj", system_prompt="P"),
                AgentConfigSchema(agent_id="node_d", name="Merger D", role="Synthesizer", objective="Obj", system_prompt="P"),
            ],
            connections=[
                Connection(source="node_a", target="node_b"),
                Connection(source="node_a", target="node_c"),
                Connection(source="node_b", target="node_d"),
                Connection(source="node_c", target="node_d"),
            ],
        )

        d_received_prompt = []

        def mock_llm(prompt, state, tools):
            current = state.get("current_agent")
            if current == "node_d":
                d_received_prompt.append(prompt)
            return f"Output_{current}"

        result = self.engine.run_architecture(arch, {"user_prompt": "Parallel processing"}, llm_runner=mock_llm)

        self.assertEqual(result.status, ExecutionStatus.SUCCESS)
        self.assertEqual(result.total_steps, 4)

        # Node D must have received outputs from both parallel branches B and C
        self.assertTrue(len(d_received_prompt) > 0)
        self.assertIn("[node_b Output]: Output_node_b", d_received_prompt[0])
        self.assertIn("[node_c Output]: Output_node_c", d_received_prompt[0])
        self.assertEqual(result.final_output, "Output_node_d")

    def test_4_mid_sem_demo_two_different_architectures_same_engine(self):
        """
        MID-SEM DEMO REQUIREMENT:
        Execute TWO DIFFERENT architectures using the SAME execution engine instance.
        """
        engine_instance = ExecutionEngine()

        # Architecture 1: 2-Agent Sequential Pipeline
        arch_1 = ArchitectureSpec(
            architecture_id="demo_arch_1_pipeline",
            task_id="demo_task_1",
            topology=TopologyType.PIPELINE,
            agents=[
                AgentConfigSchema(agent_id="p1", name="P1", role="Planner", objective="O", system_prompt="P"),
                AgentConfigSchema(agent_id="p2", name="P2", role="Executor", objective="O", system_prompt="P"),
            ],
            connections=[Connection(source="p1", target="p2")],
        )

        # Architecture 2: 4-Agent Parallel Graph Topology
        arch_2 = ArchitectureSpec(
            architecture_id="demo_arch_2_parallel",
            task_id="demo_task_2",
            topology=TopologyType.PARALLEL,
            agents=[
                AgentConfigSchema(agent_id="root", name="Root", role="Root", objective="O", system_prompt="P"),
                AgentConfigSchema(agent_id="b1", name="B1", role="Worker 1", objective="O", system_prompt="P"),
                AgentConfigSchema(agent_id="b2", name="B2", role="Worker 2", objective="O", system_prompt="P"),
                AgentConfigSchema(agent_id="join", name="Join", role="Aggregator", objective="O", system_prompt="P"),
            ],
            connections=[
                Connection(source="root", target="b1"),
                Connection(source="root", target="b2"),
                Connection(source="b1", target="join"),
                Connection(source="b2", target="join"),
            ],
        )

        def mock_llm(prompt, state, tools):
            return f"DemoResult_{state.get('current_agent')}"

        # Execute Arch 1 on engine_instance
        res_1 = engine_instance.run_architecture(arch_1, {"user_prompt": "Run Arch 1"}, llm_runner=mock_llm)
        self.assertEqual(res_1.status, ExecutionStatus.SUCCESS)
        self.assertEqual(res_1.total_steps, 2)
        self.assertEqual(res_1.final_output, "DemoResult_p2")

        # Execute Arch 2 on the EXACT SAME engine_instance without modifying engine code
        res_2 = engine_instance.run_architecture(arch_2, {"user_prompt": "Run Arch 2"}, llm_runner=mock_llm)
        self.assertEqual(res_2.status, ExecutionStatus.SUCCESS)
        self.assertEqual(res_2.total_steps, 4)
        self.assertEqual(res_2.final_output, "DemoResult_join")

    def test_5_invalid_dependency_raises_error(self):
        arch = ArchitectureSpec(
            architecture_id="invalid_conn_arch",
            task_id="task_err",
            topology=TopologyType.PIPELINE,
            agents=[
                AgentConfigSchema(agent_id="a1", name="A1", role="Role A1", objective="O", system_prompt="P")
            ],
            connections=[Connection(source="a1", target="non_existent_node")],
        )

        with self.assertRaises(ValueError) as ctx:
            self.engine.run_architecture(arch, {"user_prompt": "Test"})
        self.assertIn("non_existent_node", str(ctx.exception))

    def test_6_agent_failure_capture(self):
        arch = ArchitectureSpec(
            architecture_id="arch_failing",
            task_id="task_fail",
            topology=TopologyType.PIPELINE,
            agents=[
                AgentConfigSchema(agent_id="fail_agent", name="Fail Agent", role="Tester", objective="O", system_prompt="P")
            ],
            connections=[],
        )

        def failing_llm(prompt, state, tools):
            raise RuntimeError("Simulated unhandled model crash")

        result = self.engine.run_architecture(arch, {"user_prompt": "Test failure"}, llm_runner=failing_llm, max_retries=0)

        self.assertEqual(result.status, ExecutionStatus.FAILED)
        self.assertIn("Simulated unhandled model crash", result.error)
        self.assertIn("Execution failed", result.final_output)

    def test_7_retry_behavior(self):
        arch = ArchitectureSpec(
            architecture_id="arch_retry",
            task_id="task_retry",
            topology=TopologyType.PIPELINE,
            agents=[
                AgentConfigSchema(agent_id="flaky_agent", name="Flaky Agent", role="Flaky", objective="O", system_prompt="P")
            ],
            connections=[],
        )

        attempt_count = 0

        def flaky_llm(prompt, state, tools):
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count == 1:
                raise RuntimeError("Transient network glitch")
            return "Flaky agent recovered successfully!"

        result = self.engine.run_architecture(arch, {"user_prompt": "Test retry"}, llm_runner=flaky_llm, max_retries=1)

        self.assertEqual(result.status, ExecutionStatus.SUCCESS)
        self.assertEqual(result.final_output, "Flaky agent recovered successfully!")
        self.assertEqual(attempt_count, 2)
        self.assertEqual(result.metadata["retry_count"], 1)

    def test_8_result_aggregation_multiple_terminals(self):
        # Fan-out architecture with multiple terminal nodes: A -> B, A -> C
        arch = ArchitectureSpec(
            architecture_id="arch_fanout",
            task_id="task_fanout",
            topology=TopologyType.PARALLEL,
            agents=[
                AgentConfigSchema(agent_id="root", name="Root", role="Root", objective="O", system_prompt="P"),
                AgentConfigSchema(agent_id="term_1", name="T1", role="Terminal 1", objective="O", system_prompt="P"),
                AgentConfigSchema(agent_id="term_2", name="T2", role="Terminal 2", objective="O", system_prompt="P"),
            ],
            connections=[
                Connection(source="root", target="term_1"),
                Connection(source="root", target="term_2"),
            ],
        )

        def mock_llm(prompt, state, tools):
            current = state.get("current_agent")
            return f"Result_{current}"

        result = self.engine.run_architecture(arch, {"user_prompt": "Fanout task"}, llm_runner=mock_llm)

        self.assertEqual(result.status, ExecutionStatus.SUCCESS)
        self.assertIn("[term_1 Output]: Result_term_1", result.final_output)
        self.assertIn("[term_2 Output]: Result_term_2", result.final_output)

    def test_pipeline_and_parallel_executors(self):
        arch_pipe = ArchitectureSpec(
            architecture_id="arch_pipe_exec",
            task_id="task_p",
            topology=TopologyType.PIPELINE,
            agents=[
                AgentConfigSchema(agent_id="p1", name="P1", role="R1", objective="O", system_prompt="P"),
                AgentConfigSchema(agent_id="p2", name="P2", role="R2", objective="O", system_prompt="P"),
            ],
            connections=[Connection(source="p1", target="p2")],
        )

        pipe_executor = PipelineExecutor()
        res_pipe = pipe_executor.run_sync(arch_pipe, {"user_prompt": "Pipe test"}, llm_runner=lambda p, s, t: "Ok")
        self.assertEqual(res_pipe.status, ExecutionStatus.SUCCESS)

        parallel_executor = ParallelExecutor()
        res_par = parallel_executor.run_sync(arch_pipe, {"user_prompt": "Parallel test"}, llm_runner=lambda p, s, t: "Ok")
        self.assertEqual(res_par.status, ExecutionStatus.SUCCESS)

    def test_parallel_architecture_with_empty_connections(self):
        """
        Verify Member 1 compatibility for PARALLEL topology with empty connections:
        - executes all 3 agents
        - records all 3 agent outputs
        - produces 3 step-history entries
        - reaches SUCCESS
        - does not execute them sequentially (no upstream context injected between branches)
        """
        arch = ArchitectureSpec(
            architecture_id="arch_parallel_no_connections",
            task_id="task_parallel_3",
            topology=TopologyType.PARALLEL,
            agents=[
                AgentConfigSchema(agent_id="worker_1", name="Worker 1", role="Role 1", objective="O1", system_prompt="P1"),
                AgentConfigSchema(agent_id="worker_2", name="Worker 2", role="Role 2", objective="O2", system_prompt="P2"),
                AgentConfigSchema(agent_id="worker_3", name="Worker 3", role="Role 3", objective="O3", system_prompt="P3"),
            ],
            connections=[],
        )

        prompts_seen = {}

        def mock_llm(prompt, state, tools):
            current = state.get("current_agent")
            prompts_seen[current] = prompt
            return f"Result_{current}"

        result = self.engine.run_architecture(
            arch,
            {"user_prompt": "Process independent items"},
            llm_runner=mock_llm,
        )

        # 1. Reaches SUCCESS
        self.assertEqual(result.status, ExecutionStatus.SUCCESS)

        # 2. Executes all 3 agents and produces 3 step-history entries
        self.assertEqual(result.total_steps, 3)
        self.assertEqual(len(result.step_history), 3)
        step_agent_ids = {step.agent_id for step in result.step_history}
        self.assertEqual(step_agent_ids, {"worker_1", "worker_2", "worker_3"})

        # 3. Records all 3 agent outputs
        for aid in ["worker_1", "worker_2", "worker_3"]:
            self.assertIn(f"Result_{aid}", result.final_output)

        # 4. Verifies non-sequential execution: no worker receives output from another worker
        for aid, seen_prompt in prompts_seen.items():
            self.assertIn("Process independent items", seen_prompt)
            for other_aid in ["worker_1", "worker_2", "worker_3"]:
                if other_aid != aid:
                    self.assertNotIn(f"Result_{other_aid}", seen_prompt)


if __name__ == "__main__":
    unittest.main()
