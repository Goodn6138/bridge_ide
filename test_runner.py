#!/usr/bin/env python
"""
Run all tests with coverage report.
Usage: python test_runner.py
"""

import subprocess
import sys

def run_tests():
    """Run pytest with coverage"""
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--color=yes",
        "-W", "ignore::DeprecationWarning"
    ]
    
    result = subprocess.run(cmd)
    return result.returncode

if __name__ == "__main__":
    exit_code = run_tests()
    sys.exit(exit_code)
