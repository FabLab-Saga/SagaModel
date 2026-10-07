"""Run Python inside the live Blender window via the MCP for Blender add-on socket.

Usage: python3 scripts/bmcp.py file.py     (or code on stdin)
"""
import json
import socket
import sys

code = open(sys.argv[1]).read() if len(sys.argv) > 1 else sys.stdin.read()
s = socket.create_connection(("127.0.0.1", 9876), timeout=600)
s.sendall(json.dumps({"type": "execute_code", "params": {"code": code}}).encode())
buf = b""
while True:
    chunk = s.recv(1 << 20)
    if not chunk:
        break
    buf += chunk
    try:
        reply = json.loads(buf)
        break
    except ValueError:
        pass
result = reply.get("result", reply)
print(result.get("result", result) if isinstance(result, dict) else result)
sys.exit(reply.get("status") != "success")
