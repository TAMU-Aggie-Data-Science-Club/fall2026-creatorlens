"""Run the CreatorLens daily collectors once: python scripts/run_daily_collectors.py."""

from pathlib import Path
import subprocess
import sys


# Add future collector filenames here, in the order they should run.
COLLECTORS = [
    "collect_tech_cohort_daily.py",
    "collect_science_math_daily.py",
]


def main() -> int:
    scripts_dir = Path(__file__).resolve().parent
    failures = []
    for filename in COLLECTORS:
        print(f"Running {filename} ...", flush=True)
        result = subprocess.run(
            [sys.executable, "-u", str(scripts_dir / filename)],
            cwd=scripts_dir.parent,
            check=False,
        )
        if result.returncode:
            failures.append(f"{filename} (exit {result.returncode})")

    if failures:
        print("Failed collectors: " + ", ".join(failures), file=sys.stderr)
        return 1
    print("All collector commands finished successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
