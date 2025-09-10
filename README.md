# DAP-MCP Debugger MVP

This project implements a **Model Context Protocol (MCP) server** that exposes a
Python debugger (powered by `debugpy`) over the **Debug Adapter Protocol (DAP)**.
It allows AI hosts (e.g. Cursor, Claude, Gemini) to set breakpoints, launch
programs, step through code, and inspect variables.

---

## Installation & Setup

1. Clone this repository and install dependencies:

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

2. Copy config.example.json → config.json and edit as needed (paths, Python
executable). Example provided below.

3. Start the MCP server:
```bash
dap-mcp --config config.json
```

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
```

Demo Script (demo.py)
```python
import time

def add(a, b):
    c = a + b  # Set a breakpoint here!
    return c

if __name__ == "__main__":
    x = add(2, 3)
    time.sleep(1)
    print("x =", x)
```
Example MCP Calls

These examples assume dap-mcp is running and the MCP host can send tool calls.

1. Set a breakpoint
```json
{
  "file_path": "./demo.py",
  "line": 5
}
```

2. Launch the program
```json
{
  "program": "./demo.py",
  "cwd": ".",
  "args": []
}
```

3. Evaluate a variable while paused
```json
{ "expression": "a" }
```

4.Step over the current line
```json
{}
```

5. Continue execution until program ends
```json
{}
```







