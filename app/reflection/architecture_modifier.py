"""
Architecture Modifier Subsystem for Agent Forge.
Safely applies reflection recommendations to mutate and evolve ArchitectureSpec graphs for subsequent execution.
"""

import uuid
import copy
from typing import List, Dict, Any, Optional, Set
from pydantic import ValidationError
from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, Connection, TopologyType
from app.schemas.reflection import ReflectionResult, ArchitecturalRecommendation
from app.core.logging import logger


class ArchitectureModifier:
    """Applies recommendations to mutate an ArchitectureSpec directly with rigorous validation."""

    def apply_recommendations(
        self,
        architecture: ArchitectureSpec,
        recommendations: List[ArchitecturalRecommendation],
    ) -> ArchitectureSpec:
        """
        Convenience method to apply a list of recommendations directly.
        """
        dummy_reflection = ReflectionResult(
            reflection_id=f"refl_{uuid.uuid4().hex[:6]}",
            task_id=architecture.task_id,
            architecture_id=architecture.architecture_id,
            reflection_summary="Applied architectural recommendations.",
            recommendations=recommendations,
        )
        return self.mutate_architecture(architecture, dummy_reflection)

    def mutate_architecture(
        self, base_architecture: ArchitectureSpec, reflection: ReflectionResult
    ) -> ArchitectureSpec:
        """
        Applies reflection recommendations to create an improved, validated ArchitectureSpec.
        Rejects invalid mutations to guarantee graph safety.
        """
        logger.info(
            f"[MODIFIER] Mutating architecture {base_architecture.architecture_id} "
            f"with {len(reflection.recommendations)} recommendation(s)"
        )

        # Work on a deep copy to ensure isolation
        working_data = base_architecture.model_dump()
        original_agents = [AgentConfigSchema(**a) for a in working_data.get("agents", [])]
        original_connections = [Connection(**c) for c in working_data.get("connections", [])]

        mutated_agents: List[AgentConfigSchema] = [copy.deepcopy(a) for a in original_agents]
        mutated_connections: List[Connection] = [copy.deepcopy(c) for c in original_connections]
        applied_modifications: List[str] = []

        # Sort recommendations: high priority first
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_recs = sorted(
            reflection.recommendations,
            key=lambda r: priority_order.get(r.priority.lower(), 2),
        )

        for rec in sorted_recs:
            action = rec.action.upper()
            details = copy.deepcopy(rec.details) if rec.details else {}
            # Allow fallback attributes if set directly on recommendation object
            for attr in ("target_agent_id", "agent_id", "role", "tools", "capabilities", "name"):
                val = getattr(rec, attr, None)
                if val is not None and attr not in details:
                    if attr == "target_agent_id" and "agent_id" not in details:
                        details["agent_id"] = val
                    else:
                        details[attr] = val

            try:
                if action in ("ADD_AGENT", "ADD_VERIFICATION_STAGE"):
                    success, desc = self._apply_add_agent(mutated_agents, mutated_connections, details)
                    if success:
                        applied_modifications.append(desc)

                elif action == "REMOVE_AGENT":
                    success, desc = self._apply_remove_agent(mutated_agents, mutated_connections, details)
                    if success:
                        applied_modifications.append(desc)

                elif action == "ADD_TOOL":
                    success, desc = self._apply_add_tool(mutated_agents, details)
                    if success:
                        applied_modifications.append(desc)

                elif action == "REMOVE_TOOL":
                    success, desc = self._apply_remove_tool(mutated_agents, details)
                    if success:
                        applied_modifications.append(desc)

                elif action in ("CHANGE_AGENT_ROLE", "REPLACE_AGENT"):
                    success, desc = self._apply_change_role(mutated_agents, details)
                    if success:
                        applied_modifications.append(desc)

                elif action == "ADD_CONNECTION":
                    success, desc = self._apply_add_connection(mutated_agents, mutated_connections, details)
                    if success:
                        applied_modifications.append(desc)

                elif action == "REMOVE_CONNECTION":
                    success, desc = self._apply_remove_connection(mutated_connections, details)
                    if success:
                        applied_modifications.append(desc)

                elif action == "CHANGE_TOPOLOGY":
                    topo_str = details.get("topology", "pipeline")
                    working_data["topology"] = TopologyType(topo_str)
                    applied_modifications.append(f"Changed topology to {topo_str}")

            except Exception as e:
                logger.warning(f"[MODIFIER] Failed applying recommendation {action}: {e}. Skipping.")

        # Validate candidate mutated architecture
        new_arch_id = f"{base_architecture.architecture_id}_v2"
        validation_error = self._validate_architecture_integrity(mutated_agents, mutated_connections)

        if validation_error:
            logger.error(
                f"[VALIDATION] Mutated architecture failed safety validation: {validation_error}. "
                f"Rejecting modification and returning original architecture."
            )
            return base_architecture

        updated_reasoning = (
            f"{base_architecture.meta_reasoning or 'Base architecture.'} "
            f"Evolved via Member 3 Reflection: {'; '.join(applied_modifications)}."
        )

        try:
            evolved_arch = ArchitectureSpec(
                architecture_id=new_arch_id,
                task_id=base_architecture.task_id,
                topology=working_data.get("topology", base_architecture.topology),
                agents=mutated_agents,
                connections=mutated_connections,
                meta_reasoning=updated_reasoning,
            )
            logger.info(
                f"[VALIDATION] Improved architecture valid! Created {new_arch_id} with "
                f"{len(evolved_arch.agents)} agents and {len(evolved_arch.connections)} connections."
            )
            return evolved_arch

        except ValidationError as e:
            logger.error(f"[VALIDATION] Pydantic validation failed for mutated architecture: {e}")
            return base_architecture

    def _apply_add_agent(
        self,
        agents: List[AgentConfigSchema],
        connections: List[Connection],
        details: Dict[str, Any],
    ) -> (bool, str):
        """Adds a new agent to the architecture and rewires surrounding connections."""
        raw_agent_id = details.get("agent_id") or f"agent_{uuid.uuid4().hex[:6]}"
        agent_id = raw_agent_id

        # Ensure ID uniqueness
        existing_ids = {a.agent_id for a in agents}
        counter = 2
        while agent_id in existing_ids:
            agent_id = f"{raw_agent_id}_{counter}"
            counter += 1

        new_agent = AgentConfigSchema(
            agent_id=agent_id,
            name=details.get("name", "Specialist Agent"),
            role=details.get("role", "Specialist"),
            objective=details.get("objective", "Execute specialized processing"),
            system_prompt=details.get("system_prompt", "You are an autonomous specialist agent."),
            tools=details.get("tools", []),
            input_keys=details.get("input_keys", ["data"]),
            output_keys=details.get("output_keys", ["result"]),
            constraints=details.get("constraints", []),
        )
        agents.append(new_agent)
        logger.info(f"[MODIFIER] Added {new_agent.name} (ID: {agent_id})")

        # Rewiring logic:
        insert_after = details.get("insert_after")
        insert_before = details.get("insert_before")

        if insert_after and insert_before and insert_after in existing_ids and insert_before in existing_ids:
            # Check if there is a direct edge insert_after -> insert_before
            direct_edge_idx = None
            for idx, conn in enumerate(connections):
                if conn.source == insert_after and conn.target == insert_before:
                    direct_edge_idx = idx
                    break

            if direct_edge_idx is not None:
                # Replace direct edge with two edges: A -> New, New -> B
                connections.pop(direct_edge_idx)
                connections.append(Connection(source=insert_after, target=agent_id))
                connections.append(Connection(source=agent_id, target=insert_before))
            else:
                connections.append(Connection(source=insert_after, target=agent_id))
                connections.append(Connection(source=agent_id, target=insert_before))

        elif insert_after and insert_after in existing_ids:
            # Reroute existing outgoing edges from insert_after
            outgoing = [c for c in connections if c.source == insert_after]
            if outgoing:
                target = outgoing[0].target
                connections.remove(outgoing[0])
                connections.append(Connection(source=insert_after, target=agent_id))
                connections.append(Connection(source=agent_id, target=target))
            else:
                connections.append(Connection(source=insert_after, target=agent_id))

        elif insert_before and insert_before in existing_ids:
            # Reroute existing incoming edges to insert_before
            incoming = [c for c in connections if c.target == insert_before]
            if incoming:
                source = incoming[0].source
                connections.remove(incoming[0])
                connections.append(Connection(source=source, target=agent_id))
                connections.append(Connection(source=agent_id, target=insert_before))
            else:
                connections.append(Connection(source=agent_id, target=insert_before))

        elif len(agents) > 1:
            # Default: connect previous last agent to this new agent
            prev_last = agents[-2].agent_id
            connections.append(Connection(source=prev_last, target=agent_id))

        return True, f"Added agent '{agent_id}' ({new_agent.role})"

    def _apply_remove_agent(
        self,
        agents: List[AgentConfigSchema],
        connections: List[Connection],
        details: Dict[str, Any],
    ) -> (bool, str):
        """Safely removes an agent and reconnects dangling edges."""
        target_id = details.get("target_agent_id")
        if not target_id:
            return False, "No target agent specified for removal"

        if len(agents) <= 1:
            logger.warning(f"[MODIFIER] Refusing to remove agent '{target_id}': cannot leave architecture empty.")
            return False, "Refused to remove only remaining agent"

        target_agent = next((a for a in agents if a.agent_id == target_id), None)
        if not target_agent:
            return False, f"Agent '{target_id}' not found in architecture"

        # Find incoming and outgoing edges to stitch together
        incoming_sources = [c.source for c in connections if c.target == target_id]
        outgoing_targets = [c.target for c in connections if c.source == target_id]

        # Remove edges mentioning target
        connections[:] = [c for c in connections if c.source != target_id and c.target != target_id]

        # Re-stitch
        for src in incoming_sources:
            for dst in outgoing_targets:
                if src != dst and not any(c.source == src and c.target == dst for c in connections):
                    connections.append(Connection(source=src, target=dst))

        agents.remove(target_agent)
        logger.info(f"[MODIFIER] Removed agent '{target_id}'")
        return True, f"Removed redundant agent '{target_id}'"

    def _apply_add_tool(self, agents: List[AgentConfigSchema], details: Dict[str, Any]) -> (bool, str):
        """Adds a tool to a targeted agent."""
        target_id = details.get("target_agent_id")
        tool_name = details.get("tool_name")
        if not tool_name:
            return False, "No tool name provided"

        matched = False
        for agent in agents:
            if not target_id or agent.agent_id == target_id:
                if tool_name not in agent.tools:
                    agent.tools.append(tool_name)
                    matched = True
                    logger.info(f"[MODIFIER] Added tool '{tool_name}' to agent '{agent.agent_id}'")
                if target_id:
                    break

        if matched:
            return True, f"Assigned tool '{tool_name}' to agent '{target_id or 'all'}'"
        return False, f"Tool '{tool_name}' already present or agent not found"

    def _apply_remove_tool(self, agents: List[AgentConfigSchema], details: Dict[str, Any]) -> (bool, str):
        """Removes a tool from a targeted agent."""
        target_id = details.get("target_agent_id")
        tool_name = details.get("tool_name")
        if not tool_name or not target_id:
            return False, "Missing tool name or target agent ID"

        for agent in agents:
            if agent.agent_id == target_id and tool_name in agent.tools:
                agent.tools.remove(tool_name)
                logger.info(f"[MODIFIER] Removed tool '{tool_name}' from agent '{target_id}'")
                return True, f"Removed tool '{tool_name}' from agent '{target_id}'"
        return False, f"Tool '{tool_name}' not found on agent '{target_id}'"

    def _apply_change_role(self, agents: List[AgentConfigSchema], details: Dict[str, Any]) -> (bool, str):
        """Updates system prompt, objective, or role on targeted agent."""
        target_id = details.get("target_agent_id")
        if not target_id:
            return False, "No target agent specified"

        for agent in agents:
            if agent.agent_id == target_id:
                if "updated_system_prompt" in details:
                    agent.system_prompt = details["updated_system_prompt"]
                if "updated_role" in details:
                    agent.role = details["updated_role"]
                if "updated_objective" in details:
                    agent.objective = details["updated_objective"]
                logger.info(f"[MODIFIER] Updated configuration for agent '{target_id}'")
                return True, f"Updated role/prompt for agent '{target_id}'"
        return False, f"Agent '{target_id}' not found"

    def _apply_add_connection(
        self,
        agents: List[AgentConfigSchema],
        connections: List[Connection],
        details: Dict[str, Any],
    ) -> (bool, str):
        """Adds a communication edge between two existing agents with cycle prevention."""
        source = details.get("source")
        target = details.get("target")
        existing_ids = {a.agent_id for a in agents}

        if source in existing_ids and target in existing_ids and source != target:
            if any(c.source == source and c.target == target for c in connections):
                return False, f"Connection {source} -> {target} already exists"

            # Check if adding source -> target would create a cycle (i.e. target can already reach source)
            visited = set()
            queue = [target]
            while queue:
                curr = queue.pop(0)
                if curr == source:
                    logger.warning(f"[MODIFIER] Rejecting connection {source} -> {target}: would create cycle")
                    return False, f"Connection {source} -> {target} would create cycle"
                if curr in visited:
                    continue
                visited.add(curr)
                for conn in connections:
                    if conn.source == curr:
                        queue.append(conn.target)

            connections.append(Connection(source=source, target=target))
            logger.info(f"[MODIFIER] Added connection {source} -> {target}")
            return True, f"Connected {source} -> {target}"
        return False, f"Invalid connection endpoints {source} -> {target}"

    def _apply_remove_connection(
        self, connections: List[Connection], details: Dict[str, Any]
    ) -> (bool, str):
        """Removes a communication edge."""
        source = details.get("source")
        target = details.get("target")
        for idx, conn in enumerate(connections):
            if conn.source == source and conn.target == target:
                connections.pop(idx)
                logger.info(f"[MODIFIER] Removed connection {source} -> {target}")
                return True, f"Removed connection {source} -> {target}"
        return False, "Connection not found"

    def _validate_architecture_integrity(
        self, agents: List[AgentConfigSchema], connections: List[Connection]
    ) -> Optional[str]:
        """
        Validates:
        - At least 1 agent
        - Unique agent IDs
        - All connection sources and targets exist
        - No self-referential connections
        """
        if not agents:
            return "Architecture must have at least one agent"

        agent_ids = [a.agent_id for a in agents]
        if len(agent_ids) != len(set(agent_ids)):
            return f"Duplicate agent IDs detected: {agent_ids}"

        valid_ids = set(agent_ids)
        for conn in connections:
            if conn.source not in valid_ids:
                return f"Connection references non-existent source agent '{conn.source}'"
            if conn.target not in valid_ids:
                return f"Connection references non-existent target agent '{conn.target}'"
            if conn.source == conn.target:
                return f"Self-referential connection detected on agent '{conn.source}'"

        return None
