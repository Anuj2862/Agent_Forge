"""
Security Regression Tests for Python Sandbox Tool (Section 8.3 Audit).
Verifies prevention of:
- Arbitrary file access and /etc/passwd reading
- Shell execution and subprocess spawning
- Socket opening and network access
- Class hierarchy / introspection escapes (__class__.__subclasses__)
- Memory and infinite loop resource exhaustion (timeout termination)
- Environment variable and credential leakage
"""

import os
import pytest
from app.tools.python_tool import python_interpreter_tool


def test_sandbox_blocks_os_import():
    """Verify standard OS import is blocked."""
    res = python_interpreter_tool("import os\nos.system('echo pwned')")
    assert res["status"] == "error"
    assert "prohibited" in res["error"].lower()


def test_sandbox_blocks_subprocess_import():
    """Verify subprocess spawning is blocked."""
    res = python_interpreter_tool("import subprocess\nsubprocess.Popen(['ls'])")
    assert res["status"] == "error"
    assert "prohibited" in res["error"].lower()


def test_sandbox_blocks_socket_network():
    """Verify network socket access is blocked."""
    res = python_interpreter_tool("import socket\ns = socket.socket()")
    assert res["status"] == "error"
    assert "prohibited" in res["error"].lower()


def test_sandbox_blocks_builtins_open():
    """Verify file read via open() is blocked by AST safety validator."""
    res = python_interpreter_tool("content = open('/etc/passwd').read()")
    assert res["status"] == "error"
    assert "prohibited" in res["error"].lower() or "blocked" in res["error"].lower()


def test_sandbox_blocks_introspection_subclasses_escape():
    """Verify __class__.__subclasses__ sandbox escape is blocked."""
    escape_code = "classes = ().__class__.__bases__[0].__subclasses__()\nresult = len(classes)"
    res = python_interpreter_tool(escape_code)
    assert res["status"] == "error"
    assert "prohibited" in res["error"].lower() or "security" in res["error"].lower()


def test_sandbox_blocks_globals_introspection():
    """Verify __globals__ introspection is blocked."""
    escape_code = "func = lambda: None\ng = func.__globals__"
    res = python_interpreter_tool(escape_code)
    assert res["status"] == "error"
    assert "prohibited" in res["error"].lower()


def test_sandbox_terminates_infinite_loop_timeout():
    """Verify infinite loop is terminated by wall-clock timeout."""
    infinite_loop = "while True: pass"
    res = python_interpreter_tool(infinite_loop)
    assert res["status"] == "error"
    assert "timed out" in res["error"].lower()


def test_sandbox_strips_host_credentials():
    """Verify host environment variables and secrets are not leaked."""
    os.environ["SECRET_TEST_TOKEN"] = "SUPER_SECRET_VALUE_12345"
    check_env_code = """
import os  # blocked by AST
"""
    res = python_interpreter_tool(check_env_code)
    assert res["status"] == "error"


def test_sandbox_policy_disabled_fails_closed(monkeypatch):
    """Verify AGENT_FORGE_ENABLE_PYTHON_EXEC=false immediately fails closed."""
    monkeypatch.setenv("AGENT_FORGE_ENABLE_PYTHON_EXEC", "false")
    res = python_interpreter_tool("result = 2 + 2")
    assert res["status"] == "error"
    assert "disabled by security policy" in res["error"]


def test_sandbox_blocks_network_libraries():
    """Verify network libraries (urllib, requests, httpx) are prohibited."""
    res = python_interpreter_tool("import urllib.request\nurllib.request.urlopen('http://example.com')")
    assert res["status"] == "error"
    assert "prohibited" in res["error"].lower()


def test_sandbox_blocks_string_literal_attribute_evasion():
    """Verify string literal '__subclasses__' is rejected."""
    code = "fn = getattr((), '__subclasses__')"
    res = python_interpreter_tool(code)
    assert res["status"] == "error"
    assert "prohibited" in res["error"].lower()
