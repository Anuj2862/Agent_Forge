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


from app.schemas.validator import ArchitectureValidator


class ArchitectureGenerator:
    """Synthesizes an ArchitectureSpec dynamically from a TaskSpec with constraint enforcement."""

    def generate_architecture(self, task_spec: TaskSpec) -> ArchitectureSpec:
        if not task_spec:
            raise ValueError("task_spec cannot be None.")

        if not task_spec.subtasks:
            raise ValueError("TaskSpec must contain at least one subtask.")

        subtasks = task_spec.subtasks
        max_agents = task_spec.max_agents

        # Constraint enforcement: cluster subtasks if subtask count exceeds max_agents
        if max_agents is not None and max_agents > 0 and len(subtasks) > max_agents:
            subtask_groups = [[] for _ in range(max_agents)]
            for i, st in enumerate(subtasks):
                idx = min(i * max_agents // len(subtasks), max_agents - 1)
                subtask_groups[idx].append(st)
        else:
            subtask_groups = [[st] for st in subtasks]

        agents = []
        for i, group in enumerate(subtask_groups):
            # Combine group capabilities
            raw_tools: list[str] = []
            for st in group:
                raw_tools.extend(st.required_capabilities)
            # Deduplicate preserving order
            seen_tools = set()
            dedup_tools = [t for t in raw_tools if not (t in seen_tools or seen_tools.add(t))]

            # Enforce tool constraints
            if task_spec.forbidden_tools:
                dedup_tools = [t for t in dedup_tools if t not in task_spec.forbidden_tools]
            if task_spec.allowed_tools:
                dedup_tools = [t for t in dedup_tools if t in task_spec.allowed_tools]

            if len(group) == 1:
                st = group[0]
                agent_id = st.id
                name = self._agent_name(st.title)
                role = st.title
                objective = st.description
                system_prompt = (
                    f"You are the {role} in an autonomous multi-agent system.\n"
                    f"Core Objective: {objective}\n"
                    "Guidelines: Analyze the task critically, leverage assigned tools efficiently, "
                    "maintain strict factual grounding, and structure output clearly using Markdown."
                )
            else:
                agent_id = f"agent_merged_{i + 1}_{group[0].id}"
                merged_title = " & ".join(st.title for st in group)
                name = f"Composite Agent ({merged_title[:40]})"
                role = f"Combined: {merged_title}"
                objective = " Additionally: ".join(st.description for st in group)
                system_prompt = (
                    f"You are a consolidated agent handling: {merged_title}.\n"
                    f"Integrated Objectives: {objective}\n"
                    "Guidelines: Address all combined subtasks systematically, preserve critical context across stages, "
                    "and produce unified structured findings."
                )

            # If verification is required and this is the final agent, include verification in prompt
            if task_spec.require_verification and i == len(subtask_groups) - 1:
                system_prompt += (
                    "\nMandatory Verification Stage: You must independently audit the accuracy, "
                    "consistency, and factual grounding of all findings before finalizing output."
                )

            agent = AgentConfigSchema(
                agent_id=agent_id,
                name=name,
                role=role,
                objective=objective,
                system_prompt=system_prompt,
                tools=dedup_tools,
                input_keys=self._input_keys(agent_id),
                output_keys=[f"{agent_id}_output"],
                constraints=list(task_spec.constraints),
            )
            agents.append(agent)

        topology = self._select_topology(task_spec)
        connections = self._build_connections(
            agents=agents,
            topology=topology,
        )

        arch = ArchitectureSpec(
            architecture_id=f"architecture_{uuid4().hex[:8]}",
            task_id=task_spec.task_id,
            topology=topology,
            agents=agents,
            connections=connections,
            meta_reasoning=self._build_reasoning(task_spec, topology),
            version="v1",
        )

        # Validate with centralized ArchitectureValidator
        validation_result = ArchitectureValidator.validate(arch, task_spec=task_spec)
        if not validation_result.is_valid:
            error_details = "; ".join(f"[{e.code}] {e.message}" for e in validation_result.errors)
            raise ValueError(f"Generated architecture failed constraint validation: {error_details}")

        return arch

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

    @classmethod
    def _select_topology(cls, task_spec: TaskSpec) -> TopologyType:
        """
        Dynamically select topology based on task structure, subtask dependencies,
        and prior evolutionary memory experiences.
        """
        if len(task_spec.subtasks) <= 1:
            return TopologyType.PIPELINE

        # 1. Check if prior high-rated evolutionary memory recommends a specific topology
        retrieved_memories = (
            task_spec.metadata.get("retrieved_memories", [])
            if hasattr(task_spec, "metadata") and task_spec.metadata
            else []
        )
        if retrieved_memories:
            best_mem = retrieved_memories[0]
            if best_mem.get("success_rating", 0) >= 0.85 and best_mem.get("topology"):
                topo_str = best_mem["topology"].lower()
                for t in TopologyType:
                    if t.value == topo_str:
                        return t

        task_type = task_spec.task_type.value if hasattr(task_spec.task_type, "value") else str(task_spec.task_type)

        # 2. Hybrid DAG Fan-out -> Fan-in detection:
        # If task has 3+ subtasks and final subtask is synthesis/aggregation while earlier are research/gather
        if len(task_spec.subtasks) >= 3 and task_type != "data_analysis":
            last_title = task_spec.subtasks[-1].title.lower()
            if any(term in last_title for term in ["synthes", "aggreg", "report", "conclud", "summar", "verif"]):
                return TopologyType.HYBRID

        # 3. Parallel topology for independent research or data exploration
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

        if topology == TopologyType.HYBRID:
            # Hybrid DAG: all parallel upstream workers fan-in into the final aggregator agent
            aggregator = agents[-1]
            connections = []
            for worker in agents[:-1]:
                connections.append(
                    Connection(
                        source=worker.agent_id,
                        target=aggregator.agent_id,
                        condition=None,
                    )
                )
            return connections

        # Pipeline: each agent passes its output to the next agent in sequence.
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
        """Explain why the architecture was synthesized with specific structural characteristics."""
        memories = (
            task_spec.metadata.get("retrieved_memories", [])
            if hasattr(task_spec, "metadata") and task_spec.metadata
            else []
        )
        memory_note = (
            f" Informed by {len(memories)} prior high-success evolutionary run(s)."
            if memories
            else ""
        )

        task_type_val = (
            task_spec.task_type.value
            if hasattr(task_spec.task_type, "value")
            else str(task_spec.task_type)
        )

        if topology == TopologyType.HYBRID:
            return (
                f"The task is classified as {task_type_val} with {len(task_spec.subtasks)} subtasks. "
                "Independent exploratory agents operate in parallel before converging into an aggregator "
                f"for final synthesis and verification (Hybrid DAG Fan-In).{memory_note}"
            )

        if topology == TopologyType.PARALLEL:
            return (
                f"The task is classified as {task_type_val}. "
                "Its subtasks can be handled independently across isolated execution paths, so a parallel "
                f"multi-agent topology was selected.{memory_note}"
            )

        return (
            f"The task is classified as {task_type_val}. "
            "Its subtasks form a sequential dependency chain, so an ordered "
            f"pipeline topology was synthesized.{memory_note}"
        )
