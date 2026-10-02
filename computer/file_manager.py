
from pathlib import Path


HOME = Path.home()

APPROVED_DIRECTORIES = {
    "desktop": HOME / "Desktop",
    "documents": HOME / "Documents",
    "downloads": HOME / "Downloads",
}


def get_directory(name):
    name = name.strip().lower()

    if name not in APPROVED_DIRECTORIES:
        raise ValueError("Directory is not approved.")

    path = APPROVED_DIRECTORIES[name]

    if not path.is_dir():
        raise FileNotFoundError(
            f"Directory not found: {path}"
        )

    return path


def list_files(directory_name):
    directory = get_directory(directory_name)

    entries = []

    for item in directory.iterdir():
        entries.append({
            "name": item.name,
            "type": "folder" if item.is_dir() else "file"
        })

    return entries


def read_text_file(directory_name, filename):
    directory = get_directory(directory_name)
    path = (directory / filename).resolve()

    if path.parent != directory.resolve():
        raise ValueError("Nested or external paths are not allowed.")

    if not path.is_file():
        raise FileNotFoundError("File does not exist.")

    if path.suffix.lower() not in {
        ".txt", ".md", ".log", ".csv", ".json"
    }:
        raise ValueError("This file type is not supported.")

    if path.stat().st_size > 1_000_000:
        raise ValueError("File is too large to read.")

    return path.read_text(encoding="utf-8", errors="replace")