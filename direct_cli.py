#!/usr/bin/env python3
"""
Direct CLI Client for DAP MCP Debugger

This CLI bypasses the MCP protocol and communicates directly with the debugger.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Optional, Dict, Any, List
import argparse

try:
    import readline
except ImportError:
    readline = None

# Import the debugger components directly
sys.path.append(str(Path(__file__).parent / "src"))
from dap_mcp.config import DebuggerSpecificConfig
from dap_mcp.debugger import Debugger
from dap_mcp.factory import DAPClientSingletonFactory
from dap_types import LaunchRequestArguments
from pydantic import TypeAdapter


class DirectDAPClient:
    """Direct CLI client that uses the debugger directly."""
    
    def __init__(self, config_path: str, verbose: bool = False):
        self.config_path = Path(config_path)
        self.verbose = verbose
        self.debugger: Optional[Debugger] = None
        self.config: Optional[DebuggerSpecificConfig] = None
        self.initialized = False
        
    async def initialize(self) -> bool:
        """Initialize the debugger directly."""
        try:
            # Load configuration
            with open(self.config_path, "r") as config_file:
                debug_config_type_adapter = TypeAdapter(DebuggerSpecificConfig)
                json_config = json.load(config_file)
                self.config = debug_config_type_adapter.validate_python(json_config)
            
            # Create debugger
            dap_factory = DAPClientSingletonFactory(
                self.config.debuggerPath, 
                self.config.debuggerArgs
            )
            launch_arguments = LaunchRequestArguments(
                noDebug=False,
                **self.config.model_dump(
                    exclude_none=True,
                    exclude={"debuggerPath", "debuggerArgs", "sourceDirs", "tools"},
                ),
            )
            self.debugger = Debugger(dap_factory, launch_arguments, self.config.tools)
            
            # Initialize the debugger
            await self.debugger.initialize()
            self.initialized = True
            
            if self.verbose:
                print("Debugger initialized successfully")
            
            return True
            
        except Exception as e:
            print(f"Failed to initialize debugger: {e}")
            return False
    
    async def cleanup(self):
        """Clean up the debugger."""
        if self.debugger:
            try:
                await self.debugger.terminate()
            except:
                pass
        self.initialized = False
    
    def ensure_file_path(self, str_path: str) -> Path:
        """Ensure the file path is resolved correctly."""
        path = Path(str_path)
        if not path.is_file():
            if path.is_absolute():
                raise FileNotFoundError(f"File not found: {path}")
            if self.config is None:
                raise FileNotFoundError(f"File not found: {path}")
            for potential_dir in self.config.sourceDirs:
                potential_path = Path(potential_dir) / path
                if potential_path.is_file():
                    return potential_path
            raise FileNotFoundError(f"File not found: {path}")
        return path
    
    async def set_breakpoint(self, file_path: str, line: int, condition: Optional[str] = None) -> bool:
        """Set a breakpoint at the specified file and line."""
        if not self.initialized or not self.debugger:
            print("Debugger not initialized")
            return False
        
        try:
            resolved_path = self.ensure_file_path(file_path)
            response = await self.debugger.set_breakpoint(resolved_path, line, condition)
            
            if hasattr(response, 'render'):
                result = response.render()
            else:
                result = str(response)
            
            print(f"Breakpoint set at {file_path}:{line}")
            if condition:
                print(f"  Condition: {condition}")
            if self.verbose:
                print(f"  Response: {result}")
            return True
            
        except Exception as e:
            print(f"Failed to set breakpoint: {e}")
            return False
    
    async def remove_breakpoint(self, file_path: str, line: int) -> bool:
        """Remove a breakpoint from the specified file and line."""
        if not self.initialized or not self.debugger:
            print("Debugger not initialized")
            return False
        
        try:
            resolved_path = self.ensure_file_path(file_path)
            response = await self.debugger.remove_breakpoint(resolved_path, line)
            
            if hasattr(response, 'render'):
                result = response.render()
            else:
                result = str(response)
            
            print(f"Breakpoint removed from {file_path}:{line}")
            if self.verbose:
                print(f"  Response: {result}")
            return True
            
        except Exception as e:
            print(f"Failed to remove breakpoint: {e}")
            return False
    
    async def list_breakpoints(self) -> List[Dict[str, Any]]:
        """List all current breakpoints."""
        if not self.initialized or not self.debugger:
            print("Debugger not initialized")
            return []
        
        try:
            response = await self.debugger.list_all_breakpoints()
            
            if hasattr(response, 'render'):
                result = response.render()
            else:
                result = str(response)
            
            # Parse breakpoints from the response
            breakpoints = []
            if isinstance(response, dict):
                for file_path, bp_list in response.items():
                    for bp in bp_list:
                        breakpoints.append({
                            "file": str(file_path),
                            "line": bp.line if hasattr(bp, 'line') else 'unknown'
                        })
            
            return breakpoints
            
        except Exception as e:
            print(f"Failed to list breakpoints: {e}")
            return []
    
    async def launch_debugger(self) -> bool:
        """Launch the debugger with the configured program."""
        if not self.initialized or not self.debugger:
            print("Debugger not initialized")
            return False
        
        try:
            response = await self.debugger.launch()
            
            if hasattr(response, 'render'):
                result = response.render()
            else:
                result = str(response)
            
            print("Debugger launched successfully")
            if self.verbose:
                print(f"  Response: {result}")
            
            # The launch method should handle everything, but let's check the state
            print("Checking debugger state...")
            if hasattr(self.debugger, 'state'):
                print(f"Debugger state: {self.debugger.state}")
                
            # If still in before_launch, try to continue
            if hasattr(self.debugger, 'state') and self.debugger.state == "before_launch":
                print("Still in before_launch state, trying to continue...")
                continue_response = await self.debugger.continue_execution()
                if self.verbose:
                    print(f"  Continue response: {continue_response}")
            else:
                print("Program execution started successfully")
            
            return True
            
        except Exception as e:
            print(f"Failed to launch debugger: {e}")
            return False
    
    async def continue_execution(self) -> bool:
        """Continue execution in the debugger."""
        if not self.initialized or not self.debugger:
            print("Debugger not initialized")
            return False
        
        try:
            response = await self.debugger.continue_execution()
            
            if hasattr(response, 'render'):
                result = response.render()
            else:
                result = str(response)
            
            print("Execution continued")
            if self.verbose:
                print(f"  Response: {result}")
            return True
            
        except Exception as e:
            print(f"Failed to continue execution: {e}")
            return False
    
    async def step_over(self) -> bool:
        """Step over the current line."""
        if not self.initialized or not self.debugger:
            print("Debugger not initialized")
            return False
        
        try:
            response = await self.debugger.next()
            
            if hasattr(response, 'render'):
                result = response.render()
            else:
                result = str(response)
            
            print("Stepped over line")
            if self.verbose:
                print(f"  Response: {result}")
            return True
            
        except Exception as e:
            print(f"Failed to step over: {e}")
            return False
    
    async def step_in(self) -> bool:
        """Step into the current function."""
        if not self.initialized or not self.debugger:
            print("Debugger not initialized")
            return False
        
        try:
            response = await self.debugger.step_in()
            
            if hasattr(response, 'render'):
                result = response.render()
            else:
                result = str(response)
            
            print("Stepped into function")
            if self.verbose:
                print(f"  Response: {result}")
            return True
            
        except Exception as e:
            print(f"Failed to step in: {e}")
            return False
    
    async def step_out(self) -> bool:
        """Step out of the current function."""
        if not self.initialized or not self.debugger:
            print("Debugger not initialized")
            return False
        
        try:
            response = await self.debugger.step_out()
            
            if hasattr(response, 'render'):
                result = response.render()
            else:
                result = str(response)
            
            print("Stepped out of function")
            if self.verbose:
                print(f"  Response: {result}")
            return True
            
        except Exception as e:
            print(f"Failed to step out: {e}")
            return False
    
    async def evaluate_expression(self, expression: str) -> str:
        """Evaluate an expression in the current debugging context."""
        if not self.initialized or not self.debugger:
            return "Debugger not initialized"
        
        try:
            response = await self.debugger.evaluate(expression)
            
            if hasattr(response, 'render'):
                result = response.render()
            else:
                result = str(response)
            
            return result
            
        except Exception as e:
            return f"Error: {e}"
    
    async def view_file(self, file_path: str, line: int) -> str:
        """View file content around the specified line."""
        if not self.initialized or not self.debugger:
            return "Debugger not initialized"
        
        try:
            resolved_path = self.ensure_file_path(file_path)
            response = await self.debugger.view_file_around_line(resolved_path, line)
            
            if hasattr(response, 'render'):
                result = response.render()
            else:
                result = str(response)
            
            return result
            
        except Exception as e:
            return f"Error: {e}"


class DirectCLI:
    """Interactive CLI for the direct DAP debugger."""
    
    def __init__(self, client: DirectDAPClient):
        self.client = client
        self.running = True
        
    def print_help(self):
        """Print help information."""
        help_text = """
DAP Direct Debugger CLI Commands:

Breakpoints:
  break <file> <line> [condition]  - Set breakpoint at file:line
  clear <file> <line>              - Remove breakpoint at file:line
  list                             - List all breakpoints

Execution Control:
  run                              - Launch the debugger
  continue, c                      - Continue execution
  step, s                          - Step over (next line)
  stepin, si                       - Step into function
  stepout, so                      - Step out of function

Inspection:
  eval <expression>                - Evaluate expression
  view <file> <line>               - View file around line

General:
  help, h                          - Show this help
  quit, q                          - Exit the debugger
  status                           - Show connection status
"""
        print(help_text)
    
    async def handle_command(self, command: str) -> bool:
        """Handle a single command. Returns False if should quit."""
        parts = command.strip().split()
        if not parts:
            return True
        
        cmd = parts[0].lower()
        
        try:
            if cmd in ["help", "h"]:
                self.print_help()
                
            elif cmd in ["quit", "q", "exit"]:
                print("Goodbye!")
                return False
                
            elif cmd == "status":
                status = "Initialized" if self.client.initialized else "Not initialized"
                print(f"Status: {status}")
                
            elif cmd == "break":
                if len(parts) < 3:
                    print("Usage: break <file> <line> [condition]")
                    return True
                
                file_path = parts[1]
                try:
                    line = int(parts[2])
                    condition = parts[3] if len(parts) > 3 else None
                    await self.client.set_breakpoint(file_path, line, condition)
                except ValueError:
                    print("Line number must be an integer")
                    
            elif cmd == "clear":
                if len(parts) < 3:
                    print("Usage: clear <file> <line>")
                    return True
                
                file_path = parts[1]
                try:
                    line = int(parts[2])
                    await self.client.remove_breakpoint(file_path, line)
                except ValueError:
                    print("Line number must be an integer")
                    
            elif cmd == "list":
                breakpoints = await self.client.list_breakpoints()
                if breakpoints:
                    print("Current breakpoints:")
                    for bp in breakpoints:
                        print(f"  {bp['file']}:{bp['line']}")
                else:
                    print("No breakpoints set")
                    
            elif cmd == "run":
                await self.client.launch_debugger()
                
            elif cmd == "launch":
                # Manual launch command for debugging
                await self.client.launch_debugger()
                
            elif cmd in ["continue", "c"]:
                await self.client.continue_execution()
                
            elif cmd in ["step", "s"]:
                await self.client.step_over()
                
            elif cmd in ["stepin", "si"]:
                await self.client.step_in()
                
            elif cmd in ["stepout", "so"]:
                await self.client.step_out()
                
            elif cmd == "eval":
                if len(parts) < 2:
                    print("Usage: eval <expression>")
                    return True
                
                expression = " ".join(parts[1:])
                result = await self.client.evaluate_expression(expression)
                print(f"Result: {result}")
                
            elif cmd == "view":
                if len(parts) < 3:
                    print("Usage: view <file> <line>")
                    return True
                
                file_path = parts[1]
                try:
                    line = int(parts[2])
                    source = await self.client.view_file(file_path, line)
                    print(source)
                except ValueError:
                    print("Line number must be an integer")
                    
            else:
                print(f"Unknown command: {cmd}")
                print("Type 'help' for available commands")
                
        except Exception as e:
            print(f"Error executing command: {e}")
            
        return True
    
    async def run_interactive(self):
        """Run the interactive CLI."""
        print("DAP Direct Debugger CLI")
        print("Type 'help' for commands, 'quit' to exit")
        print()
        
        # Setup readline for better input experience (if available)
        if readline:
            readline.parse_and_bind("tab: complete")
        
        while self.running:
            try:
                command = input("(dap) ").strip()
                if command:
                    self.running = await self.handle_command(command)
            except KeyboardInterrupt:
                print("\nUse 'quit' to exit")
            except EOFError:
                break
        
        await self.client.cleanup()


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Direct DAP Debugger CLI Client")
    parser.add_argument("--config", "-c", default="config.json", 
                       help="Path to debugger configuration file")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--command", help="Execute a single command and exit")
    
    args = parser.parse_args()
    
    # Check if config file exists
    config_path = Path(args.config)
    if not config_path.exists():
        print(f"Error: Configuration file '{config_path}' not found")
        sys.exit(1)
    
    # Create and initialize client
    client = DirectDAPClient(str(config_path), args.verbose)
    
    if not await client.initialize():
        print("Failed to initialize debugger")
        sys.exit(1)
    
    try:
        cli = DirectCLI(client)
        
        if args.command:
            # Execute single command
            await cli.handle_command(args.command)
        else:
            # Run interactive mode
            await cli.run_interactive()
            
    finally:
        await client.cleanup()


if __name__ == "__main__":
    asyncio.run(main())