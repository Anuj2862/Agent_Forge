"""
Parallel Topology Executor (Owned by Member 2).
Handles parallel branch execution and fan-in aggregation.
"""

import logging
from typing import Any, Callable, Dict, Optional
from app.agents.agent_factory import AgentFactory, tool_registry
from app.agents.base_agent import BaseAgent
from app.execution.communication_graph import CommunicationGraphBuilder
from app.schemas.architecture import ArchitectureSpec
from app.schemas.execution import ExecutionResult

logger = logging.getLogger("agent_forge.execution")


class ParallelExecutor:
    """Executes parallel branch architectures with fan-in aggregation."""

    def __init__(
        self,
        factory: Optional[AgentFactory] = None,
        graph_builder: Optional[CommunicationGraphBuilder] = None,
    ):
        self.factory = factory or AgentFactory(registry=tool_registry)
        self.graph_builder = graph_builder or CommunicationGraphBuilder()

    def run_sync(
        self,
        architecture: ArchitectureSpec,
        initial_state: Dict[str, Any],
        agents: Optional[Dict[str, BaseAgent]] = None,
        llm_runner: Optional[Callable] = None,
        max_retries: int = 1,
    ) -> ExecutionResult:
        """Synchronously executes parallel architecture."""
        from app.execution.execution_engine import ExecutionEngine

        engine = ExecutionEngine(factory=self.factory, graph_builder=self.graph_builder)
        return engine.run_architecture(
            architecture=architecture,
            input_data=initial_state,
            agents=agents,
            llm_runner=llm_runner,
            max_retries=max_retries,
        )

    async def run(
        self,
        architecture: ArchitectureSpec,
        initial_state: Dict[str, Any],
        agents: Optional[Dict[str, BaseAgent]] = None,
        llm_runner: Optional[Callable] = None,
        max_retries: int = 1,
    ) -> ExecutionResult:
        """Asynchronously executes parallel architecture."""
        return self.run_sync(
            architecture=architecture,
            initial_state=initial_state,
            agents=agents,
            llm_runner=llm_runner,
            max_retries=max_retries,
        )
