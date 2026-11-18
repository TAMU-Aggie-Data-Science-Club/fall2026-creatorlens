"""Run each adopted CreatorLens dataset importer."""

import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]

# Add future dataset import scripts here after they are ready to run.
INGEST_SCRIPTS = (
    "ingest_trending_dataset.py",
)


def main():
    for script_name in INGEST_SCRIPTS:
        script = PROJECT_ROOT / "scripts" / script_name
        print(f"Running {script_name}...", flush=True)
        subprocess.run([sys.executable, str(script)], cwd=PROJECT_ROOT, check=True)


if __name__ == "__main__":
    main()
