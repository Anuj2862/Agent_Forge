"""
Base Agent Interface & Dynamic Runtime Execution (Owned by Member 2).
Provides dynamic agent execution for arbitrary roles, system prompts, and injected tools.
"""

import os
import time
from typing import Any, Callable, Dict, List, Optional
from app.core.config import settings
from app.schemas.architecture import AgentConfigSchema
from app.schemas.execution_event import ExecutionEventType, ExecutionStage


class BaseAgent:
    """
    Dynamic runtime wrapper representing an executable agent of any role.
    Role-agnostic: instantiated dynamically from AgentConfigSchema specifications.
    """

    def __init__(
        self,
        config: AgentConfigSchema,
        tools: Optional[List[Callable]] = None,
        llm_runner: Optional[Callable] = None,
    ):
        if not config or not isinstance(config, AgentConfigSchema):
            raise ValueError("BaseAgent requires a valid AgentConfigSchema instance.")
        if not config.agent_id or not config.agent_id.strip():
            raise ValueError("AgentConfigSchema must contain a non-empty agent_id.")

        self.config = config
        self.agent_id = config.agent_id
        self.name = config.name
        self.role = config.role
        self.objective = config.objective
        self.system_prompt = config.system_prompt
        self.tool_names = config.tools
        self.input_keys = config.input_keys
        self.output_keys = config.output_keys
        self.constraints = config.constraints

        self.tools: List[Callable] = tools or []
        self._llm_runner = llm_runner

    def _default_mock_llm(self, prompt: str, state: Dict[str, Any]) -> str:
        """Deterministic mock response used when no LLM runner or API key is configured."""
        tool_str = f" using tools: {self.tool_names}" if self.tool_names else ""
        return (
            f"[{self.role} ({self.agent_id}) Response]\n"
            f"Objective: {self.objective}\n"
            f"Processed prompt: '{prompt}'{tool_str}.\n"
            f"Execution completed successfully for input keys: {self.input_keys}."
        )

    def _call_llm(self, prompt: str, state: Dict[str, Any]) -> str:
        """Invokes injected llm_runner, live Gemini API if key is present, or mock fallback."""
        if self._llm_runner is not None:
            return self._llm_runner(prompt, state, self.tools)

        api_key = os.getenv("GEMINI_API_KEY") or getattr(settings, "GEMINI_API_KEY", None)

        if api_key:
            try:
                from google import genai

                client = genai.Client(api_key=api_key)
                model_name = getattr(settings, "GEMINI_MODEL", "gemini-1.5-pro")
                full_contents = f"System: {self.system_prompt}\nUser: {prompt}"
                response = client.models.generate_content(model=model_name, contents=full_contents)
                return response.text
            except Exception as e:
                return f"[{self.role} Error]: Gemini API call failed - {str(e)}"

        return self._default_mock_llm(prompt, state)

    async def execute(self, state: Dict[str, Any], emitter: Optional[Any] = None) -> Dict[str, Any]:
        """
        Executes the agent logic asynchronously over the provided state context.

        Args:
            state: Dictionary containing execution state and context.
            emitter: Optional ExecutionEventEmitter for live streaming telemetry.

        Returns:
            Dict containing step execution summary, output, tool calls, and state updates.
        """
        start_time = time.time()
        tool_call_logs: List[Dict[str, Any]] = []
        error_msg: Optional[str] = None
        status = "completed"

        active_emitter = emitter or state.get("emitter")

        # Emit agent.started event if emitter is active
        if active_emitter:
            try:
                active_emitter.emit_sync(
                    event_type=ExecutionEventType.AGENT_STARTED,
                    message=f"Agent '{self.name}' ({self.role}) initialized and running",
                    stage=ExecutionStage.AGENT_EXECUTION.value,
                    agent_id=self.agent_id,
                    data={
                        "name": self.name,
                        "role": self.role,
                        "objective": self.objective,
                        "tools": self.tool_names,
                    },
                )
            except Exception:
                pass

        # 1. Extract prompt input based on input_keys or default prompt keys
        user_prompt = state.get("user_prompt") or state.get("task_prompt") or ""
        input_context_parts = []
        for key in self.input_keys:
            if key in state:
                input_context_parts.append(f"{key}: {state[key]}")

        combined_input = user_prompt
        if input_context_parts:
            combined_input += "\nContext:\n" + "\n".join(input_context_parts)

        # 2. Intentional Tool Execution
        # Only invoke tools that match the agent's specific objective and are permitted by constraints
        forbidden_in_constraints = {
            c.lower().replace("forbidden_tool:", "").strip()
            for c in self.constraints
            if "forbidden" in c.lower()
        }

        for tool_func in self.tools:
            tool_name = getattr(tool_func, "__name__", str(tool_func)).lower()

            # Constraint check
            if any(fb in tool_name for fb in forbidden_in_constraints):
                continue

            # Intentionality check: does the agent role/objective actually warrant this tool?
            role_obj_text = f"{self.role} {self.objective} {self.name}".lower()
            is_relevant = False
            if "search" in tool_name or "web" in tool_name:
                is_relevant = any(kw in role_obj_text for kw in ["search", "retriev", "gather", "research", "investigat", "find", "ev claims"])
            elif "python" in tool_name or "interpret" in tool_name:
                is_relevant = any(kw in role_obj_text for kw in ["python", "code", "calculat", "math", "comput", "data", "script"])
            elif "document" in tool_name or "retriev" in tool_name:
                is_relevant = any(kw in role_obj_text for kw in ["document", "doc", "paper", "text", "file", "retriev"])
            else:
                is_relevant = True

            # If tool is explicitly assigned to this agent and relevant:
            if is_relevant:
                tool_start = time.time()
                tool_input = user_prompt
                if "search" in tool_name or "web" in tool_name:
                    tool_input = self.objective if self.objective else user_prompt
                elif "python" in tool_name or "interpret" in tool_name:
                    tool_input = state.get("code") or (
                        f"# Script for {self.role}\nresult = '{self.objective[:50]} processed'"
                    )

                if active_emitter:
                    try:
                        active_emitter.emit_sync(
                            event_type=ExecutionEventType.TOOL_STARTED,
                            message=f"Invoking tool '{tool_name}'",
                            stage=ExecutionStage.AGENT_EXECUTION.value,
                            agent_id=self.agent_id,
                            data={"tool": tool_name, "input_preview": str(tool_input)[:200]},
                        )
                    except Exception:
                        pass

                try:
                    if "search" in tool_name or "web" in tool_name:
                        tool_res = tool_func(query=tool_input)
                    elif "python" in tool_name or "interpret" in tool_name:
                        tool_res = tool_func(code=tool_input)
                    else:
                        tool_res = tool_func(tool_input)

                    tool_duration = round(time.time() - tool_start, 4)
                    tool_status = "success"
                    if isinstance(tool_res, dict) and tool_res.get("status") in ("error", "unavailable"):
                        tool_status = tool_res.get("status")

                    tool_call_logs.append(
                        {
                            "tool": tool_name,
                            "input": str(tool_input)[:200],
                            "result": tool_res,
                            "status": tool_status,
                            "duration_seconds": tool_duration,
                        }
                    )

                    if active_emitter:
                        try:
                            if tool_status == "error":
                                active_emitter.emit_sync(
                                    event_type=ExecutionEventType.TOOL_FAILED,
                                    message=f"Tool '{tool_name}' failed or was unavailable",
                                    stage=ExecutionStage.AGENT_EXECUTION.value,
                                    agent_id=self.agent_id,
                                    data={"tool": tool_name, "duration_seconds": tool_duration},
                                    error=str(tool_res.get("error", "tool failed")),
                                )
                            else:
                                active_emitter.emit_sync(
                                    event_type=ExecutionEventType.TOOL_COMPLETED,
                                    message=f"Tool '{tool_name}' completed in {tool_duration}s",
                                    stage=ExecutionStage.AGENT_EXECUTION.value,
                                    agent_id=self.agent_id,
                                    data={
                                        "tool": tool_name,
                                        "duration_seconds": tool_duration,
                                        "output_preview": str(tool_res)[:200],
                                    },
                                )
                        except Exception:
                            pass
                except Exception as te:
                    tool_duration = round(time.time() - tool_start, 4)
                    tool_call_logs.append(
                        {
                            "tool": tool_name,
                            "input": str(tool_input)[:200],
                            "error": str(te),
                            "status": "error",
                            "duration_seconds": tool_duration,
                        }
                    )
                    if active_emitter:
                        try:
                            active_emitter.emit_sync(
                                event_type=ExecutionEventType.TOOL_FAILED,
                                message=f"Tool '{tool_name}' raised an unhandled exception",
                                stage=ExecutionStage.AGENT_EXECUTION.value,
                                agent_id=self.agent_id,
                                data={"tool": tool_name, "duration_seconds": tool_duration},
                                error=str(te),
                            )
                        except Exception:
                            pass

        # 3. Invoke LLM for output generation
        try:
            llm_output = self._call_llm(combined_input, state)
        except Exception as e:
            error_msg = f"LLM execution error: {str(e)}"
            llm_output = f"Execution failed: {error_msg}"
            status = "failed"

        execution_duration = round(time.time() - start_time, 4)

        # 4. Prepare state updates respecting output_keys
        updated_state = dict(state)
        updated_state["current_agent"] = self.agent_id

        if self.output_keys:
            for out_key in self.output_keys:
                updated_state[out_key] = llm_output

        agent_outputs = dict(updated_state.get("agent_outputs", {}))
        agent_outputs[self.agent_id] = llm_output
        updated_state["agent_outputs"] = agent_outputs
        updated_state["final_output"] = llm_output

        # Emit agent.completed event
        if active_emitter:
            try:
                active_emitter.emit_sync(
                    event_type=ExecutionEventType.AGENT_COMPLETED,
                    message=f"Agent '{self.name}' completed execution in {execution_duration}s",
                    stage=ExecutionStage.AGENT_EXECUTION.value,
                    agent_id=self.agent_id,
                    data={
                        "status": status,
                        "duration_seconds": execution_duration,
                        "tool_call_count": len(tool_call_logs),
                        "output_preview": llm_output[:300],
                    },
                )
            except Exception:
                pass

        return {
            "agent_id": self.agent_id,
            "agent_role": self.role,
            "output": llm_output,
            "updated_state": updated_state,
            "tool_calls": tool_call_logs,
            "status": status,
            "execution_time_seconds": execution_duration,
            "error": error_msg,
        }

    def run(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronous wrapper around execute() for convenience."""
        import asyncio

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                return asyncio.run_coroutine_threadsafe(self.execute(state), loop).result()
            return loop.run_until_complete(self.execute(state))
        except RuntimeError:
            return asyncio.run(self.execute(state))
