# DAP-MCP Debugger MVP

This project implements a **Model Context Protocol (MCP) server** that exposes a
Python debugger (powered by `debugpy`) over the **Debug Adapter Protocol (DAP)**.
It allows AI hosts (e.g. Cursor, Claude, Gemini) to set breakpoints, launch
programs, step through code, and inspect variables.

## Features (Week-6 MVP)

- ✅ Launch Python programs under `debugpy`
- ✅ Set / clear breakpoints
- ✅ Pause execution and inspect variables
- ✅ Step over, step in, step out, continue, and terminate
- ✅ Return call stack and scopes

This satisfies the **Week-6 milestone** in the proposal:
> *“Build an initial Debug Adapter Protocol (DAP) MVP using debugpy.”*

---

## Installation & Setup

1. Clone this repository and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

2. Copy config.example.json → config.json and edit as needed (paths, Python
executable). Example provided below.

3. Start the MCP server:
```bash
dap-mcp --config config.json

4. Connect with an MCP host (Cursor, Claude Desktop, or custom client).

Example Config (config.example.json)
```jsonc
{
  "type": "debugpy",
  "debuggerPath": "./.venv/Scripts/python.exe", // Path to your Python interpreter
  "debuggerArgs": ["-m", "debugpy.adapter"],
  "sourceDirs": ["./src"],

  // Program to run by default when calling `launch` with no args
  "program": "./demo.py",
  "cwd": ".",

  // Optional environment variables (enable UTF-8 on Windows)
  "env": {
    "PYTHONUTF8": "1"
  }
}



