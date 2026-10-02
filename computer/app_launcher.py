
import subprocess


APPROVED_APPS = {
    "notepad": ["notepad.exe"],
    "calculator": ["calc.exe"],
    "paint": ["mspaint.exe"],
    "file explorer": ["explorer.exe"],
    "task manager": ["taskmgr.exe"],
    "command prompt": ["cmd.exe"],
}


def launch_app(name):
    name = name.strip().lower()

    if name not in APPROVED_APPS:
        return {
            "success": False,
            "message": f"{name} is not an approved application."
        }

    try:
        subprocess.Popen(APPROVED_APPS[name])

        return {
            "success": True,
            "message": f"Opening {name}."
        }

    except OSError as error:
        return {
            "success": False,
            "message": str(error)
        }