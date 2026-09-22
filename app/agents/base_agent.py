"""
Base Agent Interface & Dynamic Runtime Execution (Owned by Member 2).
Provides dynamic agent execution for arbitrary roles, system prompts, and injected tools.
"""

import os
import time
from typing import Any, Callable, Dict, List, Optional
from app.core.config import settings
from app.schemas.architecture import AgentConfigSchema


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

    async def execute(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """
        Executes the agent logic asynchronously over the provided state context.

        Args:
            state: Dictionary containing execution state and context.

        Returns:
            Dict containing step execution summary, output, tool calls, and state updates.
        """
        start_time = time.time()
        tool_call_logs: List[Dict[str, Any]] = []
        error_msg: Optional[str] = None
        status = "completed"

        # 1. Extract prompt input based on input_keys or default prompt keys
        user_prompt = state.get("user_prompt") or state.get("task_prompt") or ""
        input_context_parts = []
        for key in self.input_keys:
            if key in state:
                input_context_parts.append(f"{key}: {state[key]}")

        combined_input = user_prompt
        if input_context_parts:
            combined_input += "\nContext:\n" + "\n".join(input_context_parts)

        # 2. Execute tools if injected
        for tool_func in self.tools:
            tool_name = getattr(tool_func, "__name__", str(tool_func))
            try:
                if tool_name == "web_search_tool" or "search" in tool_name:
                    tool_res = tool_func(query=user_prompt or "general query")
                elif tool_name == "python_interpreter_tool" or "python" in tool_name:
                    code_snippet = state.get("code") or "print('executing python tool')"
                    tool_res = tool_func(code=code_snippet)
                else:
                    tool_res = tool_func(user_prompt)

                tool_call_logs.append(
                    {
                        "tool": tool_name,
                        "input": user_prompt,
                        "result": tool_res,
                        "status": "success",
                    }
                )
            except Exception as te:
                tool_call_logs.append(
                    {
                        "tool": tool_name,
                        "input": user_prompt,
                        "error": str(te),
                        "status": "error",
                    }
                )

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
