
import unittest

from app.tool_registry import ToolRegistry


class TestToolRegistry(unittest.TestCase):

    def setUp(self):
        self.registry = ToolRegistry()

    def test_register_and_list_tool(self):
        self.registry.register(
            name="get_status",
            description="Get a status value.",
            handler=lambda: "running",
            permission_action="system_information",
        )

        tools = self.registry.list_tools()

        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]["name"], "get_status")

    def test_execute_allowed_tool(self):
        self.registry.register(
            name="get_status",
            description="Get a status value.",
            handler=lambda: "running",
            permission_action="system_information",
        )

        result = self.registry.execute("get_status")

        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "running")

    def test_unknown_tool(self):
        result = self.registry.execute("missing_tool")

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "not_found")

    def test_missing_required_parameter(self):
        self.registry.register(
            name="greet",
            description="Greet a person.",
            handler=lambda name: f"Hello, {name}",
            permission_action="system_information",
            required_parameters=("name",),
        )

        result = self.registry.execute("greet")

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "invalid_arguments")

    def test_unexpected_parameter(self):
        self.registry.register(
            name="greet",
            description="Greet a person.",
            handler=lambda name: f"Hello, {name}",
            permission_action="system_information",
            required_parameters=("name",),
        )

        result = self.registry.execute(
            "greet",
            {"name": "Pawan", "command": "whoami"},
        )

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "invalid_arguments")

    def test_confirmation_required(self):
        called = []

        self.registry.register(
            name="security_scan",
            description="Run a security scan.",
            handler=lambda target: called.append(target),
            permission_action="run_security_scan",
            required_parameters=("target",),
        )

        result = self.registry.execute(
            "security_scan",
            {"target": "127.0.0.1"},
        )

        self.assertFalse(result["success"])
        self.assertEqual(
            result["status"],
            "confirmation_required",
        )
        self.assertEqual(called, [])

    def test_confirmed_action_executes(self):
        self.registry.register(
            name="security_scan",
            description="Run a security scan.",
            handler=lambda target: f"Scanned {target}",
            permission_action="run_security_scan",
            required_parameters=("target",),
        )

        result = self.registry.execute(
            "security_scan",
            {"target": "127.0.0.1"},
            confirmed=True,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "Scanned 127.0.0.1")

    def test_duplicate_registration_rejected(self):
        self.registry.register(
            name="get_status",
            description="Get status.",
            handler=lambda: "ok",
            permission_action="system_information",
        )

        with self.assertRaises(ValueError):
            self.registry.register(
                name="get_status",
                description="Another status tool.",
                handler=lambda: "different",
                permission_action="system_information",
            )

    def test_handler_error(self):
        def broken_handler():
            raise RuntimeError("Something went wrong.")

        self.registry.register(
            name="broken",
            description="A failing tool.",
            handler=broken_handler,
            permission_action="system_information",
        )

        result = self.registry.execute("broken")

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "execution_error")


if __name__ == "__main__":
    unittest.main()
