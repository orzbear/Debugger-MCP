# dap_client.py (Final Corrected Version)
import subprocess
import socket
import json
import time
import os

# --- Part 1: Helper functions ---
def create_dap_message(message_dict):
    message_json = json.dumps(message_dict)
    return f"Content-Length: {len(message_json)}\r\n\r\n{message_json}"

# CORRECTED a FUNCTION to use stream.read() instead of sock.recv()
def read_dap_message(stream):
    """Reads a single DAP message from a stream (like stdout)."""
    buffer = b""
    while not buffer.endswith(b'\r\n\r\n'):
        buffer += stream.read(1) # Use read() for streams
    headers_part = buffer.decode('utf-8')
    headers = {
        key.strip(): int(value.strip())
        for key, value in (line.split(":") for line in headers_part.strip().split("\r\n"))
    }
    content_length = headers['Content-Length']
    body_part = b""
    while len(body_part) < content_length:
        body_part += stream.read(content_length - len(body_part)) # Use read() here too
    return json.loads(body_part.decode('utf-8'))

# --- Part 2: Main script logic ---
# 1. Launch the debugger in ADAPTER mode. It will wait for instructions.
debugger_process = subprocess.Popen(
    ["python", "-m", "debugpy.adapter"],
    stdin=subprocess.PIPE, stdout=subprocess.PIPE
)

print("Debugger adapter process started.")

# We now communicate over stdio, not a socket.
stdin = debugger_process.stdin
stdout = debugger_process.stdout

try:
    # --- Part 3: Robust Initialization and Launch Flow ---
    
    # 2. Send 'initialize' request
    initialize_request = {"seq": 1, "type": "request", "command": "initialize", "arguments": {"adapterID": "python"}}
    stdin.write(create_dap_message(initialize_request).encode('utf-8'))
    stdin.flush()
    print("\n➡️  Sent 'initialize' request.")

    # 3. Loop until the debugger is fully initialized
    is_initialized = False
    while not is_initialized:
        msg = read_dap_message(stdout)
        print(f"⬅️  Received Message: {json.dumps(msg, indent=2)}")
        if msg.get("event") == "initialized":
            print("--- Got 'initialized' event! Debugger is ready. ---")
            is_initialized = True

    # 4. Tell the debugger to LAUNCH the program but STOP ON ENTRY
    script_path = os.path.abspath("buggy_program.py")
    launch_request = {
        "seq": 2, "type": "request", "command": "launch",
        "arguments": {
            "program": script_path,
            "stopOnEntry": True
        }
    }
    stdin.write(create_dap_message(launch_request).encode('utf-8'))
    stdin.flush()
    print("\n➡️  Sent 'launch' request with stopOnEntry=true.")
    
    # 5. Wait for the 'stopped' event due to stopOnEntry
    stopped_on_entry = False
    while not stopped_on_entry:
        msg = read_dap_message(stdout)
        print(f"⬅️  Received Message: {json.dumps(msg, indent=2)}")
        if msg.get("event") == "stopped" and msg.get("body", {}).get("reason") == "entry":
            print("--- Program stopped on entry as expected. ---")
            thread_id = msg["body"]["threadId"]
            stopped_on_entry = True

    # 6. Now that the program is paused, set our breakpoint.
    set_breakpoint_request = {
        "seq": 3, "type": "request", "command": "setBreakpoints",
        "arguments": {"source": {"path": script_path}, "breakpoints": [{"line": 8}]}
    }
    stdin.write(create_dap_message(set_breakpoint_request).encode('utf-8'))
    stdin.flush()
    print("\n➡️  Sent 'setBreakpoints' request.")
    set_breakpoint_response = read_dap_message(stdout)
    print(f"⬅️  Received setBreakpoints response:\n{json.dumps(set_breakpoint_response, indent=2)}")

    # 7. Finalize configuration
    configuration_done_request = {"seq": 4, "type": "request", "command": "configurationDone"}
    stdin.write(create_dap_message(configuration_done_request).encode('utf-8'))
    stdin.flush()
    print("\n➡️  Sent 'configurationDone' request.")
    config_done_response = read_dap_message(stdout)
    print(f"⬅️  Received configurationDone response:\n{json.dumps(config_done_response, indent=2)}")

    # 8. Tell the program to CONTINUE running.
    continue_request = {"seq": 5, "type": "request", "command": "continue", "arguments": {"threadId": thread_id}}
    stdin.write(create_dap_message(continue_request).encode('utf-8'))
    stdin.flush()
    print("\n➡️  Sent 'continue' request.")
    continue_response = read_dap_message(stdout)
    print(f"⬅️  Received continue response:\n{json.dumps(continue_response, indent=2)}")

    # 9. Wait for the program to hit our breakpoint.
    print("\n⏳ Program is running... waiting for our breakpoint hit...")
    stopped_event = read_dap_message(stdout)
    print(f"🛑 Received Message: {json.dumps(stopped_event, indent=2)}")

    # VERIFY SUCCESS
    if stopped_event.get("event") == "stopped" and stopped_event.get("body", {}).get("reason") == "breakpoint":
        print("\n🎉 SUCCESS! The program correctly stopped at the breakpoint.")
    else:
        print("\n❌ FAILURE! The program did not stop as expected.")

finally:
    # --- Part 4: Cleanup ---
    print("\nCleaning up.")
    debugger_process.terminate()
    debugger_process.wait()
    print("Cleanup complete.")