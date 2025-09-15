import json
import sys
import click
import asyncio
from contextlib import asynccontextmanager
from dap_types import LaunchRequestArguments, SourceBreakpoint
from pathlib import Path
from pydantic import TypeAdapter
from typing import Optional, TextIO, cast, AsyncGenerator

# The new high-level server is now in the 'fastmcp' module
from mcp.server.fastmcp import FastMCP, Context

from dap_mcp.config import DebuggerSpecificConfig
from dap_mcp.debugger import Debugger, FunctionCallError
from dap_mcp.factory import DAPClientSingletonFactory
from dap_mcp.render import render_xml, try_render

import logging

logger = logging.getLogger(__name__)

# Helper class to manage state attached to the context
class AppState:
    debugger: Debugger
    config: DebuggerSpecificConfig

    def ensure_file_path(self, str_path: str) -> Path | None:
        path = Path(str_path)
        if not path.is_file():
            if path.is_absolute():
                return None
            for potential_dir in self.config.sourceDirs:
                potential_path = Path(potential_dir) / path
                if potential_path.is_file():
                    return potential_path
            return None
        return path

def get_state(ctx: Context) -> AppState:
    """Safely get the typed state from the context."""
    return cast(AppState, ctx.app_state)


# Define the lifespan function as an async context manager
@asynccontextmanager
async def lifespan(app: FastMCP) -> AsyncGenerator[None, None]:
    """Handles server startup and shutdown."""
    # This is a bit of a workaround to get the config file path at startup
    @click.command()
    @click.option("--config", "-c", "config_file", help="Path to the configuration file", required=True, type=click.File("r"))
    @click.option("--verbose", "-v", is_flag=True, help="Enable verbose logging", default=False)
    def cli_wrapper(config_file: TextIO, verbose: bool):
        if verbose:
            logging.basicConfig(level=logging.DEBUG, stream=sys.stderr)

        debug_config_type_adapter: TypeAdapter[DebuggerSpecificConfig] = TypeAdapter(DebuggerSpecificConfig)
        try:
            json_config = json.load(config_file)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON configuration: {e}")
            sys.exit(1)

        config = debug_config_type_adapter.validate_python(json_config)
        dap_factory = DAPClientSingletonFactory(config.debuggerPath, config.debuggerArgs)
        launch_arguments = LaunchRequestArguments(
            noDebug=False,
            **config.model_dump(
                exclude_none=True,
                exclude={"debuggerPath", "debuggerArgs", "sourceDirs", "tools"},
            ),
        )
        debugger = Debugger(dap_factory, launch_arguments, config.tools)

        state = AppState()
        state.debugger = debugger
        state.config = config
        app.app_state = state # Attach state to the app object

    try:
        # Manually parse command-line arguments
        cli_wrapper(standalone_mode=False)
        # Initialize the debugger after loading the config
        await get_state(app).debugger.initialize()
    except click.exceptions.MissingParameter:
        print("Error: Missing --config option. Please start with 'python -m src.dap_mcp.server --config your_config.json'", file=sys.stderr)
        asyncio.get_event_loop().stop()
        yield
        return

    print("Server startup complete.")
    yield
    print("Server shutting down.")


# 1. Initialize the FastMCP Server and pass the lifespan function
app = FastMCP("dap-mcp-server", "v1.0", lifespan=lifespan)

# 2. Define all your tools with decorators (These remain the same)
@app.tool()
async def launch(ctx: Context) -> str:
    """Launch the debuggee program. Set breakpoints before launching if necessary."""
    state = get_state(ctx)
    response = await state.debugger.launch()
    return try_render(response)

@app.tool()
async def set_breakpoint(ctx: Context, path: str, line: int, condition: Optional[str] = None) -> str:
    """Set a breakpoint at the specified file and line with an optional condition."""
    state = get_state(ctx)
    file_path = state.ensure_file_path(path)
    if file_path is None:
        return FunctionCallError(message=f"File ({path}) not found").render()
    response = await state.debugger.set_breakpoint(file_path, line, condition)
    return try_render(response)

# ... (all other @app.tool() decorated functions remain exactly the same as the previous version) ...

@app.tool()
async def remove_breakpoint(ctx: Context, path: str, line: int) -> str:
    """Remove a breakpoint from the specified file and line."""
    state = get_state(ctx)
    file_path = state.ensure_file_path(path)
    if file_path is None:
        return FunctionCallError(message=f"File ({path}) not found").render()
    response = await state.debugger.remove_breakpoint(file_path, line)
    return try_render(response)

@app.tool()
async def view_file_around_line(ctx: Context, line: int, path: Optional[str] = None) -> str:
    """Returns the lines of source code around the specified line."""
    state = get_state(ctx)
    if path:
        file_path = state.ensure_file_path(path)
        if file_path is None:
            return FunctionCallError(message=f"File ({path}) not found").render()
    else:
        file_path = None
    response = await state.debugger.view_file_around_line(file_path, line)
    return try_render(response)

@app.tool()
async def remove_all_breakpoints(ctx: Context) -> str:
    """Remove all breakpoints currently set in the debugger."""
    state = get_state(ctx)
    response = await state.debugger.remove_all_breakpoints()
    if isinstance(response, FunctionCallError):
        return response.render()
    return "All breakpoints removed"

@app.tool()
async def list_all_breakpoints(ctx: Context) -> str:
    """List all breakpoints currently set in the debugger."""
    state = get_state(ctx)
    response = await state.debugger.list_all_breakpoints()
    if isinstance(response, FunctionCallError):
        return response.render()

    def render_file(file: str, breakpoints: list[SourceBreakpoint]) -> str:
        return render_xml("file", [render_xml("breakpoint", None, **sb.model_dump()) for sb in breakpoints], path=file)

    return render_xml("breakpoints", [render_file(str(file), breakpoints) for file, breakpoints in response.items()])

@app.tool()
async def continue_execution(ctx: Context) -> str:
    """Continue execution in the debugger after hitting a breakpoint."""
    state = get_state(ctx)
    response = await state.debugger.continue_execution()
    return try_render(response)

@app.tool()
async def step_in(ctx: Context) -> str:
    """Step into the function call in the debugger."""
    state = get_state(ctx)
    response = await state.debugger.step_in()
    return try_render(response)

@app.tool()
async def step_out(ctx: Context) -> str:
    """Step out of the current function in the debugger."""
    state = get_state(ctx)
    response = await state.debugger.step_out()
    return try_render(response)

@app.tool()
async def next(ctx: Context) -> str:
    """Step over to the next line of code in the debugger."""
    state = get_state(ctx)
    response = await state.debugger.next()
    return try_render(response)

@app.tool()
async def evaluate(ctx: Context, expression: str) -> str:
    """Evaluate an expression in the current debugging context."""
    state = get_state(ctx)
    response = await state.debugger.evaluate(expression)
    return try_render(response)

@app.tool()
async def change_frame(ctx: Context, frameId: int) -> str:
    """Change the current debugging frame to the specified frame ID."""
    state = get_state(ctx)
    response = await state.debugger.change_frame(frameId)
    return response.render()

@app.tool()
async def terminate(ctx: Context) -> str:
    """Terminate the current debugging session."""
    state = get_state(ctx)
    response = await state.debugger.terminate()
    if isinstance(response, FunctionCallError):
        return response.render()
    return response

@app.tool()
async def get_launch_config(ctx: Context) -> str:
    """Returns the user provided launch configuration along with its detailed schema for a DAP-compatible debugger."""
    state = get_state(ctx)
    config = state.config
    config_schema = json.dumps(type(config).model_json_schema())
    config_json = json.dumps(config.model_dump(exclude_none=True))
    return render_xml(
        "config",
        [
            render_xml("schema", config_schema),
            render_xml("data", config_json),
        ],
    )

# 3. Add a main block to run the server directly
if __name__ == "__main__":
    app.run()