# DAP MCP Debugger CLI Client

A command-line interface for interacting with the DAP MCP debugger server. This CLI provides an interactive debugging experience with commands for breakpoints, execution control, and variable inspection.

## Features

- **Breakpoint Management**: Set, remove, and list breakpoints
- **Execution Control**: Launch, continue, step through code
- **Variable Inspection**: Evaluate expressions and view source code
- **Interactive Mode**: Command-line interface with tab completion
- **Single Command Mode**: Execute individual commands

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements-cli.txt
```

2. Ensure your `config.json` file is properly configured for your debugger.

## Usage

### Interactive Mode

Start the CLI in interactive mode:

```bash
python cli_client.py --config config.json
```

This will start an interactive session where you can type commands:

```
DAP MCP Debugger CLI
Type 'help' for commands, 'quit' to exit

(dap) help
(dap) break demo.py 5
(dap) run
(dap) step
(dap) eval a + b
(dap) quit
```

### Single Command Mode

Execute a single command and exit:

```bash
python cli_client.py --config config.json --command "break demo.py 5"
```

### Simple CLI (Alternative)

For a simpler implementation without async dependencies:

```bash
python simple_cli.py --config config.json
```

## Commands

### Breakpoints
- `break <file> <line> [condition]` - Set breakpoint at file:line
- `clear <file> <line>` - Remove breakpoint at file:line
- `clearall` - Remove all breakpoints
- `list` - List all breakpoints

### Execution Control
- `run` - Launch the debugger
- `continue`, `c` - Continue execution
- `step`, `s` - Step over (next line)
- `stepin`, `si` - Step into function
- `stepout`, `so` - Step out of function

### Inspection
- `eval <expression>` - Evaluate expression
- `view <file> <line>` - View file around line
- `config` - Show debugger configuration

### General
- `help`, `h` - Show help
- `quit`, `q` - Exit the debugger
- `status` - Show connection status

## Examples

### Basic Debugging Session

```bash
# Start the CLI
python cli_client.py --config config.json

# Set a breakpoint
(dap) break demo.py 5

# Launch the debugger
(dap) run

# Step through the code
(dap) step

# Evaluate variables
(dap) eval a
(dap) eval b
(dap) eval a + b

# Continue execution
(dap) continue

# Exit
(dap) quit
```

### Setting Conditional Breakpoints

```bash
(dap) break demo.py 8 "a > 5"
```

### Viewing Source Code

```bash
(dap) view demo.py 5
```

## Configuration

The CLI uses the same `config.json` file as the MCP server. Make sure it's properly configured with:

- `debuggerPath`: Path to the debugger executable
- `debuggerArgs`: Arguments for the debugger
- `program`: Path to the program to debug
- `sourceDirs`: Directories to search for source files

## Troubleshooting

### Connection Issues

If you get connection errors:

1. Ensure the MCP server can start properly:
   ```bash
   python src/dap_mcp/server.py --config config.json --transport stdio
   ```

2. Check that all paths in `config.json` are correct and accessible.

3. Use `--verbose` flag for detailed logging:
   ```bash
   python cli_client.py --config config.json --verbose
   ```

### Command Not Found

If commands aren't recognized:

1. Make sure you're using the correct command syntax
2. Check the help with `help` command
3. Verify the MCP server is responding properly

## Architecture

The CLI client communicates with the MCP debugger server using the MCP protocol:

1. **CLI Client** (`cli_client.py`) - Full-featured async client
2. **Simple CLI** (`simple_cli.py`) - Lightweight synchronous client
3. **MCP Server** (`src/dap_mcp/server.py`) - The debugger server
4. **Configuration** (`config.json`) - Debugger settings

## Development

To extend the CLI:

1. Add new commands in the `handle_command` method
2. Implement corresponding methods in the client class
3. Update the help text
4. Test with the MCP server

## License

Same as the main DAP MCP project.
