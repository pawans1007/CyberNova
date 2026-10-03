
import unittest
from unittest.mock import Mock

from app.tool_registry import ToolRegistry


class TestToolRegistry(unittest.TestCase):

    def setUp(self):
        self.permissions = Mock()
        self.permissions.requires_confirmation.return_value = False
        self.permissions.is_allowed.return_value = True

        self.registry = ToolRegistry(
            permission_manager=self.permissions
        )

    def test_register_and_list_tool(self):
        self.registry.register(
            "get_status",
            "Get status",
            lambda: "running",
            "system_information",
        )

        self.assertEqual(
            self.registry.list_tools()[0]["name"],
            "get_status",
        )

    def test_execute_allowed_tool(self):
        self.registry.register(
            "get_status",
            "Get status",
            lambda: "running",
            "system_information",
        )

        result = self.registry.execute("get_status")

        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "running")

    def test_unknown_tool(self):
        result = self.registry.execute("missing")

        self.assertFalse(result["success"])
        self.assertEqual(result["status"], "not_found")

    def test_missing_required_parameter(self):
        self.registry.register(
            "greet",
            "Greet someone",
            lambda name: f"Hello {name}",
            "system_information",
            required_parameters=("name",),
        )

        result = self.registry.execute("greet")

        self.assertEqual(result["status"], "invalid_arguments")

    def test_unexpected_parameter(self):
        self.registry.register(
            "greet",
            "Greet someone",
            lambda name: f"Hello {name}",
            "system_information",
            required_parameters=("name",),
        )

        result = self.registry.execute(
            "greet",
            {"name": "Pawan", "extra": "value"},
        )

        self.assertEqual(result["status"], "invalid_arguments")

    def test_confirmation_required(self):
        self.permissions.requires_confirmation.return_value = True

        handler = Mock()

        self.registry.register(
            "security_scan",
            "Run a security scan",
            handler,
            "run_security_scan",
            required_parameters=("target",),
        )

        result = self.registry.execute(
            "security_scan",
            {"target": "127.0.0.1"},
        )

        self.assertEqual(
            result["status"],
            "confirmation_required",
        )
        handler.assert_not_called()

    def test_confirmed_action_executes(self):
        self.permissions.requires_confirmation.return_value = True

        self.registry.register(
            "security_scan",
            "Run a security scan",
            lambda target: f"Scanned {target}",
            "run_security_scan",
            required_parameters=("target",),
        )

        result = self.registry.execute(
            "security_scan",
            {"target": "127.0.0.1"},
            confirmed=True,
        )

        self.assertTrue(result["success"])
        self.assertEqual(result["result"], "Scanned 127.0.0.1")

    def test_duplicate_registration(self):
        self.registry.register(
            "status",
            "Get status",
            lambda: "ok",
            "system_information",
        )

        with self.assertRaises(ValueError):
            self.registry.register(
                "status",
                "Duplicate",
                lambda: "other",
                "system_information",
            )

    def test_handler_error(self):
        def broken():
            raise RuntimeError("Test error")

        self.registry.register(
            "broken",
            "Failing tool",
            broken,
            "system_information",
        )

        result = self.registry.execute("broken")

        self.assertEqual(result["status"], "execution_error")


if __name__ == "__main__":
    unittest.main()
