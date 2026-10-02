
import os
import webbrowser

from computer.app_launcher import launch_app
from computer.file_manager import list_files
from computer.system_info import get_system_info


FOLDERS = {
    "downloads": os.path.join(
        os.path.expanduser("~"), "Downloads"
    ),
    "documents": os.path.join(
        os.path.expanduser("~"), "Documents"
    ),
    "desktop": os.path.join(
        os.path.expanduser("~"), "Desktop"
    ),
}

WEBSITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "github": "https://github.com",
    "chatgpt": "https://chatgpt.com",
}


def open_folder(name):
    name = name.lower().strip()

    if name not in FOLDERS:
        return f"Folder '{name}' is not supported."

    path = FOLDERS[name]

    if not os.path.isdir(path):
        return f"Folder not found: {path}"

    try:
        os.startfile(path)
        return f"Opening {name}."
    except OSError as error:
        return f"Could not open folder: {error}"


def open_website(name):
    name = name.lower().strip()

    if name not in WEBSITES:
        return f"Website '{name}' is not approved."

    webbrowser.open(WEBSITES[name])
    return f"Opening {name}."


def execute_computer_command(command):
    command = command.strip().lower()

    if command.startswith("open "):
        target = command[5:].strip()

        if target in FOLDERS:
            return open_folder(target)

        if target in WEBSITES:
            return open_website(target)

        result = launch_app(target)
        return result["message"]

    if command in {
        "show system information",
        "system information",
    }:
        return str(get_system_info())

    if command.startswith("list files in "):
        directory = command[len("list files in "):].strip()

        try:
            files = list_files(directory)
            if not files:
                return "The folder is empty."

            return "\n".join(
                f"{item['type']}: {item['name']}"
                for item in files
            )
        except (ValueError, FileNotFoundError, OSError) as error:
            return str(error)

    return "That computer command is not supported."