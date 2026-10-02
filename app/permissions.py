from enum import Enum


class PermissionLevel(Enum):
    READ_ONLY = "read_only"
    STANDARD = "standard"
    SENSITIVE = "sensitive"


class PermissionManager:
    def __init__(self):
        self.allowed_actions = {
            "open_application",
            "open_folder",
            "open_website",
            "system_information",
        }

        self.confirmation_required = {
            "delete_file",
            "move_file",
            "write_file",
            "run_security_scan",
            "change_system_setting",
        }

    def is_allowed(self, action):
        return action in self.allowed_actions

    def requires_confirmation(self, action):
        return action in self.confirmation_required

    def describe_action(self, action):
        if self.is_allowed(action):
            return "Allowed"

        if self.requires_confirmation(action):
            return "Requires confirmation"

        return "Not authorized"