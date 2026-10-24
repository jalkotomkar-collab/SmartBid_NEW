"""Run all three test scripts and print a one-line summary.   Usage:  python tests/run_all.py"""
import pathlib
import subprocess
import sys

here = pathlib.Path(__file__).resolve().parent
failed = 0
for name in ("test_core.py", "test_auctions.py", "test_pages.py"):
    result = subprocess.run([sys.executable, str(here / name)], capture_output=True, text=True)
    last = (result.stdout.strip().splitlines() or ["(no output)"])[-1]
    print(("PASS  " if result.returncode == 0 else "FAIL  ") + f"{name}: {last}")
    if result.returncode:
        failed += 1
        print(result.stderr[-1500:])
sys.exit(1 if failed else 0)
