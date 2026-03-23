import subprocess
import sys
import os
import time

PYTHON = sys.executable

print("=== Adaptive System Launcher ===\n")

# Start Flask target server in background
print("[1/2] Starting target server on port 5000...")
server = subprocess.Popen([PYTHON, "target_server.py"])
time.sleep(2)

# Start main adaptive system
print("[2/2] Starting adaptive system on port 8000...")
print("\nDashboard: open frontend/adaptive-system.html in your browser")
print("API:       http://localhost:8000/state\n")

try:
    subprocess.run([PYTHON, "main.py"])
except KeyboardInterrupt:
    print("\nShutting down...")
    server.terminate()