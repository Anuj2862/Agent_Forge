"""
Centralized Architecture Validator for Agent Forge.
Validates structural integrity, graph topology, and hard constraints across:
- Initial Architecture Synthesis (V1)
- Architecture Mutation / Evolution (V2)
- Pre-Execution Verification
- Evolution Decision Making
"""

from typing import List, Optional, Set, Dict, Any, Union
from pydantic import BaseModel, Field

from app.schemas.architecture import ArchitectureSpec, AgentConfigSchema, Connection, TopologyType
from app.schemas.task import TaskSpec, TaskConstraints


class ValidationErrorDetail(BaseModel):
    code: str = Field(..., description="Stable error code identifier")
    message: str = Field(..., description="Human-readable explanation of validation failure")
    field: Optional[str] = Field(default=None, description="Specific field or component affected")


class ValidationResult(BaseModel):
    is_valid: bool
    errors: List[ValidationErrorDetail] = Field(default_factory=list)

    @property
    def error_messages(self) -> List[str]:
        return [f"[{e.code}] {e.message}" for e in self.errors]

    @property
    def has_errors(self) -> bool:
        return len(self.errors) > 0

    def __len__(self) -> int:
        return len(self.errors)

    def __iter__(self):
        return iter(self.errors)

    def __getitem__(self, idx):
        return self.errors[idx]


class ArchitectureValidator:
    """
    Validates an ArchitectureSpec against structural graph rules and TaskSpec constraints.
    """

    KNOWN_TOOLS: Set[str] = {
        "web_search",
        "web_search_tool",
        "python_tool",
        "python_interpreter",
        "python_interpreter_tool",
        "document_retriever",
        "document_retriever_tool",
        "calculator",
    }

    @classmethod
    def validate(
        cls,
        architecture: ArchitectureSpec,
        task_spec: Optional[TaskSpec] = None,
        constraints: Optional[Union[TaskConstraints, Dict[str, Any]]] = None,
    ) -> ValidationResult:
        errors: List[ValidationErrorDetail] = []

        agents = architecture.agents or []
        connections = architecture.connections or []

        # 1. Non-empty agent set
        if not agents:
            errors.append(
                ValidationErrorDetail(
                    code="EMPTY_AGENT_LIST",
                    message="Architecture must contain at least one agent.",
                    field="agents",
                )
            )
            return ValidationResult(is_valid=False, errors=errors)

        # 2. Agent ID uniqueness & format
        agent_ids = [a.agent_id for a in agents]
        seen_ids: Set[str] = set()
        for a in agents:
            if not a.agent_id or not a.agent_id.strip():
                errors.append(
                    ValidationErrorDetail(
                        code="EMPTY_AGENT_ID",
                        message=f"Agent '{a.name}' has an empty or blank agent_id.",
                        field="agents",
                    )
                )
            elif a.agent_id in seen_ids:
                errors.append(
                    ValidationErrorDetail(
                        code="DUPLICATE_AGENT_ID",
                        message=f"Duplicate agent ID detected: '{a.agent_id}'.",
                        field=f"agents.{a.agent_id}",
                    )
                )
            seen_ids.add(a.agent_id)

        # Resolve effective constraints
        effective_max_agents = None
        effective_forbidden_tools: Set[str] = set()
        effective_allowed_tools: Optional[Set[str]] = None
        effective_require_verification = False

        if task_spec:
            effective_max_agents = task_spec.max_agents
            effective_forbidden_tools = set(task_spec.forbidden_tools or [])
            if task_spec.allowed_tools:
                effective_allowed_tools = set(task_spec.allowed_tools)
            effective_require_verification = getattr(task_spec, "require_verification", False)

        if constraints:
            if isinstance(constraints, dict):
                c_max = constraints.get("max_agents")
                c_forbid = constraints.get("forbidden_tools")
                c_allow = constraints.get("allowed_tools")
                c_verif = constraints.get("require_verification")
            else:
                c_max = getattr(constraints, "max_agents", None)
                c_forbid = getattr(constraints, "forbidden_tools", None)
                c_allow = getattr(constraints, "allowed_tools", None)
                c_verif = getattr(constraints, "require_verification", False)
            if c_max is not None:
                effective_max_agents = c_max
            if c_forbid:
                effective_forbidden_tools.update(c_forbid)
            if c_allow is not None:
                effective_allowed_tools = set(c_allow)
            if c_verif:
                effective_require_verification = True

        # 3. Hard Constraint: Max Agents
        if effective_max_agents is not None:
            if len(agents) > effective_max_agents:
                errors.append(
                    ValidationErrorDetail(
                        code="MAX_AGENTS_EXCEEDED",
                        message=(
                            f"Architecture has {len(agents)} agents, violating the task's hard constraint "
                            f"limit of {effective_max_agents} agents maximum."
                        ),
                        field="agents",
                    )
                )

        # 4. Tool Constraints (Allowed vs Forbidden)
        for a in agents:
            for tool in a.tools:
                # Check forbidden
                if tool in effective_forbidden_tools or any(fb in tool for fb in effective_forbidden_tools):
                    errors.append(
                        ValidationErrorDetail(
                            code="FORBIDDEN_TOOL_USED",
                            message=f"Agent '{a.agent_id}' is assigned forbidden tool '{tool}'.",
                            field=f"agents.{a.agent_id}.tools",
                        )
                    )
                # Check allowed list if specified
                if effective_allowed_tools is not None and tool not in effective_allowed_tools:
                    errors.append(
                        ValidationErrorDetail(
                            code="DISALLOWED_TOOL_ASSIGNED",
                            message=f"Agent '{a.agent_id}' is assigned tool '{tool}' not in allowed list: {list(effective_allowed_tools)}.",
                            field=f"agents.{a.agent_id}.tools",
                        )
                    )

        # 5. Connection Integrity
        valid_agent_ids = seen_ids
        for idx, conn in enumerate(connections):
            if conn.source not in valid_agent_ids:
                errors.append(
                    ValidationErrorDetail(
                        code="INVALID_EDGE_SOURCE",
                        message=f"Connection {idx} references non-existent source agent '{conn.source}'.",
                        field=f"connections[{idx}].source",
                    )
                )
            if conn.target not in valid_agent_ids:
                errors.append(
                    ValidationErrorDetail(
                        code="INVALID_EDGE_TARGET",
                        message=f"Connection {idx} references non-existent target agent '{conn.target}'.",
                        field=f"connections[{idx}].target",
                    )
                )
            if conn.source == conn.target:
                errors.append(
                    ValidationErrorDetail(
                        code="SELF_LOOP_DETECTED",
                        message=f"Self-referential connection detected on agent '{conn.source}'.",
                        field=f"connections[{idx}]",
                    )
                )

        # 6. Cycle Detection (DAG enforcement)
        adjacency: Dict[str, List[str]] = {aid: [] for aid in valid_agent_ids}
        for conn in connections:
            if conn.source in adjacency:
                adjacency[conn.source].append(conn.target)

        has_cycle, cycle_path = cls._detect_cycle(adjacency)
        if has_cycle:
            errors.append(
                ValidationErrorDetail(
                    code="CYCLE_DETECTED",
                    message=f"Graph topology contains an illegal cycle: {' -> '.join(cycle_path)}.",
                    field="connections",
                )
            )

        # 7. Verification Requirement Enforcement
        needs_verification = effective_require_verification
        if not needs_verification and task_spec and task_spec.constraints:
            c_strs = task_spec.constraints if isinstance(task_spec.constraints, list) else []
            if any(
                phrase in c.lower()
                for c in c_strs
                for phrase in [
                    "require verification",
                    "requires verification",
                    "mandatory verification",
                    "require fact verification",
                    "require_verification",
                ]
            ):
                needs_verification = True

        if needs_verification:
            has_verifier = any(
                any(
                    v in (a.role + " " + a.name + " " + a.objective + " " + a.system_prompt).lower()
                    for v in ["verif", "fact_check", "validator"]
                )
                for a in agents
            )
            if not has_verifier:
                errors.append(
                    ValidationErrorDetail(
                        code="REQUIRED_VERIFICATION_MISSING",
                        message="Task requires an independent verification stage, but no verification agent was found.",
                        field="agents",
                    )
                )

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)

    @classmethod
    def _detect_cycle(cls, adjacency: Dict[str, List[str]]) -> tuple[bool, List[str]]:
        """DFS cycle detection returning boolean and cycle path if found."""
        visited: Dict[str, int] = {k: 0 for k in adjacency}  # 0: unvisited, 1: visiting, 2: visited
        path: List[str] = []

        def dfs(node: str) -> bool:
            visited[node] = 1
            path.append(node)
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    continue
                if visited[neighbor] == 1:
                    path.append(neighbor)
                    return True
                if visited[neighbor] == 0:
                    if dfs(neighbor):
                        return True
            path.pop()
            visited[node] = 2
            return False

        for node in adjacency:
            if visited[node] == 0:
                if dfs(node):
                    return True, path

        return False, []
