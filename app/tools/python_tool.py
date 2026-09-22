"""
Python Code Interpreter Tool Primitive (Owned by Member 2).
Executes Python code in a safe, restricted local context and captures stdout/errors.
"""

import ast
import io
import sys
from typing import Any, Dict

# Prohibited modules and attributes for unsafe execution prevention
PROHIBITED_IMPORTS = {"os", "sys", "subprocess", "shutil", "socket", "builtins", "importlib", "pty", "commands"}


def _check_safety(code: str) -> None:
    """Basic AST safety check to prevent shell/OS command execution."""
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return  # Syntax error will be caught during execution

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.split(".")[0] in PROHIBITED_IMPORTS:
                    raise PermissionError(f"Import of module '{alias.name}' is prohibited for safety.")
        elif isinstance(node, ast.ImportFrom):
            if node.module and node.module.split(".")[0] in PROHIBITED_IMPORTS:
                raise PermissionError(f"Import from module '{node.module}' is prohibited for safety.")
        elif isinstance(node, ast.Attribute):
            if node.attr in {"system", "popen", "execvp", "execv", "spawn", "rmtree"}:
                raise PermissionError(f"Use of prohibited attribute '{node.attr}'.")


def python_interpreter_tool(code: str) -> Dict[str, Any]:
    """
    Executes Python code string and returns structured output capturing stdout and errors.

    Args:
        code: Python code string to execute.

    Returns:
        Dict with status, result, stdout, and error fields.
    """
    if not isinstance(code, str) or not code.strip():
        return {
            "status": "error",
            "result": None,
            "stdout": "",
            "error": "Code string must be non-empty.",
        }

    try:
        _check_safety(code)
    except PermissionError as pe:
        return {
            "status": "error",
            "result": None,
            "stdout": "",
            "error": f"Security restriction: {str(pe)}",
        }

    old_stdout = sys.stdout
    redirected_output = io.StringIO()
    sys.stdout = redirected_output

    exec_globals: Dict[str, Any] = {"__builtins__": __builtins__}
    exec_locals: Dict[str, Any] = {}

    try:
        # Try evaluating as a single expression first (e.g., 2 + 2)
        try:
            compiled_expr = compile(code, "<string>", "eval")
            result = eval(compiled_expr, exec_globals, exec_locals)
            captured_stdout = redirected_output.getvalue()
            return {
                "status": "success",
                "result": str(result) if result is not None else captured_stdout.strip(),
                "stdout": captured_stdout,
                "error": None,
            }
        except SyntaxError:
            # Fall back to multi-line statement execution
            exec(code, exec_globals, exec_locals)
            captured_stdout = redirected_output.getvalue()
            result_val = exec_locals.get("result") or captured_stdout.strip()
            return {
                "status": "success",
                "result": str(result_val) if result_val is not None else "Execution completed successfully.",
                "stdout": captured_stdout,
                "error": None,
            }
    except Exception as e:
        captured_stdout = redirected_output.getvalue()
        return {
            "status": "error",
            "result": None,
            "stdout": captured_stdout,
            "error": f"{type(e).__name__}: {str(e)}",
        }
    finally:
        sys.stdout = old_stdout
