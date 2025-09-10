# dap-mcp

**dap-mcp** is an implementation of the [Model Context Protocol (MCP)](https://example.com/mcp-spec) tailored for managing Debug Adapter Protocol (DAP) sessions. MCP provides a standardized framework to optimize and extend the context window of large language models, and in this project, it is used to enhance and streamline debugging workflows.

## Features

- **Debug Adapter Protocol Integration:** Interact with debuggers using a standardized protocol.
- **MCP Framework:** Leverage MCP to optimize context and enhance debugging workflows.
- **Rich Debugging Tools:** Set, list, and remove breakpoints; control execution (continue, step in/out/next); evaluate expressions; change stack frames; and view source code.
- **Flexible Configuration:** Customize debugger settings, source directories, and other parameters via a JSON configuration file.
## Installation

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (optional, for running the server)

### Installing and Running the Server

Install **dap-mcp** and its dependencies:

```bash
pip install dap-mcp
python -m dap_mcp --config config.json

# Or, if you have uv installed
uvx dap-mcp@latest --config config.json