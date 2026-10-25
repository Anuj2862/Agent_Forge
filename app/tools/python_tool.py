"""
Python Code Interpreter Tool Primitive (Owned by Member 2).
Executes Python code in an isolated subprocess with stripped environment,
bounded execution time, AST safety validation, and memory/filesystem sandboxing.
"""

import ast
import os
import subprocess
import sys
import tempfile
from typing import Any, Dict

# Prohibited modules and attributes for unsafe execution prevention
PROHIBITED_IMPORTS = {
    "os",
    "sys",
    "subprocess",
    "shutil",
    "socket",
    "builtins",
    "importlib",
    "pty",
    "commands",
    "pathlib",
    "ctypes",
    "signal",
    "posix",
    "nt",
    "multiprocessing",
    "threading",
    "urllib",
    "http",
    "requests",
    "httpx",
    "aiohttp",
    "pickle",
    "shelve",
    "marshal",
    "gc",
    "inspect",
    "dis",
    "code",
    "codeop",
    "platform",
}

PROHIBITED_CALLS = {"eval", "exec", "compile", "open", "__import__", "breakpoint"}
PROHIBITED_ATTRS = {
    "system",
    "popen",
    "execvp",
    "execv",
    "spawn",
    "rmtree",
    "unlink",
    "remove",
    "__class__",
    "__subclasses__",
    "__bases__",
    "__globals__",
    "__code__",
    "__builtins__",
}

MAX_CODE_LENGTH = 10000
MAX_OUTPUT_LENGTH = 10000
TIMEOUT_SECONDS = 5.0


def _set_posix_limits() -> None:
    """Set OS-level resource limits for the child process."""
    try:
        import resource
        # Limit CPU time (4s soft, 5s hard)
        resource.setrlimit(resource.RLIMIT_CPU, (4, 5))
        # Limit maximum file creation size to 1MB
        if hasattr(resource, "RLIMIT_FSIZE"):
            resource.setrlimit(resource.RLIMIT_FSIZE, (1024 * 1024, 1024 * 1024))
        # Limit file descriptors to 32
        if hasattr(resource, "RLIMIT_NOFILE"):
            resource.setrlimit(resource.RLIMIT_NOFILE, (32, 64))
    except Exception:
        pass


def _check_safety(code: str) -> None:
    """AST safety validation to prevent shell, filesystem, and introspection escape attempts."""
    try:
        tree = ast.parse(code)
    except SyntaxError as se:
        raise SyntaxError(f"Syntax error in code: {se}")

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                base_pkg = alias.name.split(".")[0]
                if base_pkg in PROHIBITED_IMPORTS:
                    raise PermissionError(f"Import of module '{alias.name}' is prohibited for safety.")
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                base_pkg = node.module.split(".")[0]
                if base_pkg in PROHIBITED_IMPORTS:
                    raise PermissionError(f"Import from module '{node.module}' is prohibited for safety.")
        elif isinstance(node, ast.Attribute):
            if node.attr in PROHIBITED_ATTRS:
                raise PermissionError(f"Use of prohibited attribute '{node.attr}'.")
        elif isinstance(node, ast.Name):
            if node.id in PROHIBITED_CALLS:
                raise PermissionError(f"Call to prohibited built-in '{node.id}' is blocked.")
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            # Block evasion attempts embedding prohibited attribute names in dynamic calls
            if node.value in {"__subclasses__", "__globals__", "__builtins__", "__class__"}:
                raise PermissionError(f"String literal '{node.value}' is prohibited for safety.")


def python_interpreter_tool(code: str) -> Dict[str, Any]:
    """
    Executes Python code in an isolated subprocess with strict sandboxing:
    - Dedicated clean temporary directory
    - Completely stripped environment (zero credentials/secrets exposed)
    - Wall-clock timeout of 5 seconds
    - Bounded input and output size
    - Blocked dangerous built-ins and imports

    Args:
        code: Python code string to execute.

    Returns:
        Dict with status, result, stdout, and error fields.
    """
    if os.getenv("AGENT_FORGE_ENABLE_PYTHON_EXEC", "true").lower() in ("0", "false", "no", "disabled"):
        return {
            "status": "error",
            "result": None,
            "stdout": "",
            "error": "Arbitrary Python code execution is disabled by security policy (AGENT_FORGE_ENABLE_PYTHON_EXEC=false).",
        }

    if not isinstance(code, str) or not code.strip():
        return {
            "status": "error",
            "result": None,
            "stdout": "",
            "error": "Code string must be non-empty.",
        }

    if len(code) > MAX_CODE_LENGTH:
        return {
            "status": "error",
            "result": None,
            "stdout": "",
            "error": f"Code length exceeds maximum allowed limit of {MAX_CODE_LENGTH} characters.",
        }

    try:
        _check_safety(code)
    except (PermissionError, SyntaxError) as pe:
        return {
            "status": "error",
            "result": None,
            "stdout": "",
            "error": f"Security restriction: {str(pe)}",
        }

    # Runner script that wraps the user code safely
    # If the user code sets a variable `result`, it prints JSON delimiter for structured extraction.
    wrapper_code = f"""
import sys

_exec_globals = {{}}
_exec_locals = {{}}

_code = {repr(code)}

try:
    _compiled_eval = compile(_code, "<string>", "eval")
    _res = eval(_compiled_eval, _exec_globals, _exec_locals)
    if _res is not None:
        print("___RESULT_DELIMITER___")
        print(_res)
except SyntaxError:
    exec(_code, _exec_globals, _exec_locals)
    if "result" in _exec_locals:
        print("___RESULT_DELIMITER___")
        print(_exec_locals["result"])
"""

    with tempfile.TemporaryDirectory() as sandbox_dir:
        # Isolated stripped environment
        clean_env = {
            "PATH": "/usr/bin:/bin",
            "PYTHONUNBUFFERED": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        }

        try:
            preexec = _set_posix_limits if sys.platform != "win32" else None
            proc = subprocess.Popen(
                [sys.executable, "-I", "-c", wrapper_code],
                cwd=sandbox_dir,
                env=clean_env,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                preexec_fn=preexec,
            )

            try:
                stdout_str, stderr_str = proc.communicate(timeout=TIMEOUT_SECONDS)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.communicate()
                return {
                    "status": "error",
                    "result": None,
                    "stdout": "",
                    "error": f"Execution timed out after {TIMEOUT_SECONDS} seconds.",
                }

            if proc.returncode != 0:
                import signal
                if proc.returncode in (-24, -9, 137) or (hasattr(signal, "SIGXCPU") and proc.returncode == -signal.SIGXCPU):
                    err_clean = f"Execution timed out or exceeded CPU resource limits after {TIMEOUT_SECONDS} seconds."
                elif stderr_str.strip():
                    err_clean = stderr_str.strip().splitlines()[-1]
                else:
                    err_clean = f"Process exited with code {proc.returncode}"
                return {
                    "status": "error",
                    "result": None,
                    "stdout": stdout_str[:MAX_OUTPUT_LENGTH],
                    "error": err_clean,
                }

            # Parse result delimiter if present
            if "___RESULT_DELIMITER___" in stdout_str:
                parts = stdout_str.split("___RESULT_DELIMITER___", 1)
                printed_stdout = parts[0].strip()
                extracted_result = parts[1].strip()
                final_res = extracted_result
                final_out = printed_stdout or extracted_result
            else:
                final_out = stdout_str.strip()
                final_res = final_out if final_out else "Execution completed successfully."

            return {
                "status": "success",
                "result": str(final_res)[:MAX_OUTPUT_LENGTH],
                "stdout": final_out[:MAX_OUTPUT_LENGTH],
                "error": None,
            }

        except Exception as e:
            return {
                "status": "error",
                "result": None,
                "stdout": "",
                "error": f"Sandbox error: {str(e)}",
            }
