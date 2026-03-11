import signal
import subprocess
import sys
import time
from pathlib import Path


def main():
    project_root = Path(__file__).resolve().parents[2]
    next_app_dir = project_root / "frontend" / "next_app"

    procs = []

    api_proc = subprocess.Popen(
        ["uvicorn", "frontend.api_server:app", "--port", "6305"],
        cwd=str(project_root),
    )
    procs.append(api_proc)

    npm_proc = subprocess.Popen(
        ["npm", "run", "dev"],
        cwd=str(next_app_dir),
    )
    procs.append(npm_proc)

    def shutdown(*_):
        for p in procs:
            p.terminate()
        sys.exit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    while True:
        for p in procs:
            if p.poll() is not None:
                shutdown()
        time.sleep(0.5)
