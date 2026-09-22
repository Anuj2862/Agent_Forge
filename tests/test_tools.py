"""
Unit Tests for Member 2 Tool Registry & Prototype Tools.
"""

import unittest
from unittest.mock import patch, MagicMock
from app.tools.tool_registry import ToolRegistry, tool_registry
from app.tools.python_tool import python_interpreter_tool
from app.tools.web_search import web_search_tool
from app.tools.document_retriever import document_retriever_tool


class TestToolRegistry(unittest.TestCase):

    def setUp(self):
        self.registry = ToolRegistry()

    def test_register_and_get_tool(self):
        def sample_tool(x: int) -> int:
            return x * 2

        self.registry.register("sample", sample_tool)
        retrieved = self.registry.get_tool("sample")
        self.assertEqual(retrieved, sample_tool)
        self.assertEqual(retrieved(5), 10)

    def test_get_multiple_tools(self):
        def tool_a(): return "a"
        def tool_b(): return "b"

        self.registry.register("tool_a", tool_a)
        self.registry.register("tool_b", tool_b)

        tools = self.registry.get_tools(["tool_a", "tool_b"])
        self.assertEqual(len(tools), 2)
        self.assertEqual(tools[0](), "a")
        self.assertEqual(tools[1](), "b")

    def test_unknown_tool_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.registry.get_tool("non_existent_tool")

    def test_duplicate_registration_prevention(self):
        def dummy1(): pass
        def dummy2(): pass

        self.registry.register("dummy", dummy1)
        with self.assertRaises(ValueError):
            self.registry.register("dummy", dummy2)

        # Overwrite allowed when overwrite=True
        self.registry.register("dummy", dummy2, overwrite=True)
        self.assertEqual(self.registry.get_tool("dummy"), dummy2)

    def test_list_tools_and_has_tool(self):
        self.registry.register("t1", lambda: 1)
        self.registry.register("t2", lambda: 2)

        self.assertTrue(self.registry.has_tool("t1"))
        self.assertFalse(self.registry.has_tool("t3"))
        self.assertEqual(sorted(self.registry.list_tools()), ["t1", "t2"])

    def test_clear_registry(self):
        self.registry.register("t1", lambda: 1)
        self.registry.clear()
        self.assertEqual(self.registry.list_tools(), [])

    def test_global_tool_registry_default_tools(self):
        # Global registry should automatically have default tools registered
        self.assertTrue(tool_registry.has_tool("web_search"))
        self.assertTrue(tool_registry.has_tool("python_tool"))
        self.assertTrue(tool_registry.has_tool("document_retriever"))

        tools = tool_registry.get_tools(["web_search", "python_tool"])
        self.assertEqual(len(tools), 2)


class TestPythonInterpreterTool(unittest.TestCase):

    def test_simple_calculation_expression(self):
        res = python_interpreter_tool("2 + 3 * 4")
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"], "14")
        self.assertIsNone(res["error"])

    def test_statement_execution_with_result_variable(self):
        code = "a = 10\nb = 20\nresult = a + b"
        res = python_interpreter_tool(code)
        self.assertEqual(res["status"], "success")
        self.assertEqual(res["result"], "30")
        self.assertIsNone(res["error"])

    def test_stdout_capture(self):
        code = "print('Hello, Agent Forge!')"
        res = python_interpreter_tool(code)
        self.assertEqual(res["status"], "success")
        self.assertIn("Hello, Agent Forge!", res["stdout"])

    def test_error_handling_division_by_zero(self):
        res = python_interpreter_tool("1 / 0")
        self.assertEqual(res["status"], "error")
        self.assertIn("ZeroDivisionError", res["error"])

    def test_empty_input_handling(self):
        res = python_interpreter_tool("   ")
        self.assertEqual(res["status"], "error")
        self.assertIn("non-empty", res["error"])

    def test_security_restriction_prohibited_import(self):
        res = python_interpreter_tool("import os\nos.system('dir')")
        self.assertEqual(res["status"], "error")
        self.assertIn("Security restriction", res["error"])


class TestWebSearchTool(unittest.TestCase):

    def test_web_search_callable_interface_empty_query(self):
        res = web_search_tool("")
        self.assertEqual(res["status"], "error")
        self.assertIn("non-empty", res["error"])

    @patch.dict("os.environ", {}, clear=True)
    def test_web_search_offline_response_without_api_key(self):
        res = web_search_tool("Agent Forge Architecture")
        self.assertEqual(res["status"], "no_credentials")
        self.assertEqual(len(res["results"]), 1)
        self.assertIn("Offline Result", res["results"][0]["title"])

    @patch.dict("os.environ", {"TAVILY_API_KEY": "test-tavily-key"})
    @patch("httpx.post")
    def test_web_search_successful_mocked_http_response(self, mock_post):
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "results": [
                {"title": "Agent AI Paper", "content": "Generative Agents overview", "url": "https://example.com/paper"}
            ]
        }
        mock_post.return_value = mock_response

        res = web_search_tool("Multi-Agent Frameworks")
        self.assertEqual(res["status"], "success")
        self.assertEqual(len(res["results"]), 1)
        self.assertEqual(res["results"][0]["title"], "Agent AI Paper")
        mock_post.assert_called_once()

    @patch.dict("os.environ", {"TAVILY_API_KEY": "invalid-key"})
    @patch("httpx.post")
    def test_web_search_http_failure_handling(self, mock_post):
        mock_post.side_effect = Exception("API rate limit reached")

        res = web_search_tool("Test Query")
        self.assertEqual(res["status"], "error")
        self.assertIn("API rate limit reached", res["error"])


if __name__ == "__main__":
    unittest.main()
