# CyberNova — desktop assistant project

## Quick start (Windows)
1. Extract this folder somewhere writable.
2. Install Python 3.11 or 3.12 (recommended for dependency compatibility).
3. Double-click `SETUP_CYBERNOVA.bat`.
4. Double-click `START_CYBERNOVA.bat`.

Ollama is optional for local LLM chat. Install Ollama separately and pull the model configured in `config.py` (currently `qwen2.5:3b-instruct`). Start Ollama before using local-model features.

## Included modules
- PySide6 desktop interface and chat
- Ollama client and intent routing
- Voice recognition/speech output modules (microphone and audio dependencies may require OS setup)
- Computer and file utilities
- Browser/search utilities
- Memory and automation modules
- Authorized cybersecurity lab manager, scanner, scan history, and report generation
- Existing tests

## Important status note
This package is based on the uploaded source project. It is **not a claim that every requested capability is already fully integrated or verified**. In particular, broad natural-language computer control, end-to-end voice command execution, robust browser interaction, persistent automation workflows, and standalone packaging still require implementation and integration testing. The included cybersecurity scanner requires Nmap and should only be used against explicitly authorized lab targets. It does not provide unrestricted attack functionality.

## Tests
From this folder, after setup:
```powershell
.venv\Scripts\python.exe -m unittest discover -s test -v
```

## Project layout
The source is organized into `app`, `ai`, `ui`, `voice`, `computer`, `web`, `cybersecurity`, `memory`, and `automation`. Runtime databases and reports are created locally as needed. Do not place API keys or passwords in source files.
