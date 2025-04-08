#!/usr/bin/env python3
"""
Helper script to run tests with the correct Python path
"""

import os
import sys
import subprocess

# Add the src directory to the Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SRC_DIR = os.path.join(BASE_DIR, "src")
sys.path.insert(0, SRC_DIR)

# Run pytest with the specified arguments
def run_tests():
    test_args = sys.argv[1:] if len(sys.argv) > 1 else ["tests/"]
    cmd = ["python3", "-m", "pytest"] + test_args
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, env=dict(os.environ, PYTHONPATH=SRC_DIR))
    return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())
