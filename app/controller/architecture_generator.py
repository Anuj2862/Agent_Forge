"""
Architecture Generator Subsystem (Owned by Member 1).
"""

from uuid import uuid4

from app.schemas.task import TaskSpec
from app.schemas.architecture import (
    ArchitectureSpec,
    AgentConfigSchema,
    Connection,
    TopologyType,
)


class ArchitectureGenerator:
    """Synthesizes an ArchitectureSpec dynamically from a TaskSpec."""

    def generate_architecture(self, task_spec: TaskSpec) -> ArchitectureSpec:
        if not task_spec:
            raise ValueError("task_spec cannot be None.")

        if not task_spec.subtasks:
            raise ValueError("TaskSpec must contain at least one subtask.")

        agents = []

        for subtask in task_spec.subtasks:
            tools = list(subtask.required_capabilities)

            agent = AgentConfigSchema(
                agent_id=subtask.id,
                name=self._agent_name(subtask.title),
                role=subtask.title,
                objective=subtask.description,
                system_prompt=(
                    f"You are responsible for the task: {subtask.title}. "
                    f"{subtask.description}"
                ),
                tools=tools,
                input_keys=self._input_keys(subtask.id),
                output_keys=[f"{subtask.id}_output"],
                constraints=list(task_spec.constraints),
            )

            agents.append(agent)

        topology = self._select_topology(task_spec)

        connections = self._build_connections(
            agents=agents,
            topology=topology,
        )

        return ArchitectureSpec(
            architecture_id=f"architecture_{uuid4().hex[:8]}",
            task_id=task_spec.task_id,
            topology=topology,
            agents=agents,
            connections=connections,
            meta_reasoning=self._build_reasoning(task_spec, topology),
        )

    @staticmethod
    def _agent_name(title: str) -> str:
        """Convert a subtask title into a readable agent name."""
        words = title.strip().split()

        if not words:
            return "Task Agent"

        return " ".join(word.capitalize() for word in words) + " Agent"

    @staticmethod
    def _input_keys(subtask_id: str) -> list[str]:
        """Return the input keys for an agent."""
        return [f"{subtask_id}_input"]

    @staticmethod
    def _select_topology(task_spec: TaskSpec) -> TopologyType:
        """
        Select a topology based on task structure.

        Sequential subtasks use a pipeline.
        Multiple independent subtasks use parallel execution.
        """

        if len(task_spec.subtasks) <= 1:
            return TopologyType.PIPELINE

        task_type = task_spec.task_type.value

        parallel_task_types = {
            "research",
            "data_analysis",
        }

        if task_type in parallel_task_types:
            return TopologyType.PARALLEL

        return TopologyType.PIPELINE

    @staticmethod
    def _build_connections(
        agents: list[AgentConfigSchema],
        topology: TopologyType,
    ) -> list[Connection]:
        """Build connections according to the selected topology."""

        if len(agents) <= 1:
            return []

        if topology == TopologyType.PARALLEL:
            # Parallel agents execute independently.
            return []

        # Pipeline: each agent passes its output to the next agent.
        connections = []

        for current_agent, next_agent in zip(agents, agents[1:]):
            connections.append(
                Connection(
                    source=current_agent.agent_id,
                    target=next_agent.agent_id,
                    condition=None,
                )
            )

        return connections

    @staticmethod
    def _build_reasoning(
        task_spec: TaskSpec,
        topology: TopologyType,
    ) -> str:
        """Explain why the architecture was selected."""

        if topology == TopologyType.PARALLEL:
            return (
                f"The task is classified as {task_spec.task_type.value}. "
                "Its subtasks can be handled independently, so a parallel "
                "multi-agent topology was selected."
            )

        return (
            f"The task is classified as {task_spec.task_type.value}. "
            "Its subtasks are represented as an ordered workflow, so a "
            "pipeline topology was selected."
        )
