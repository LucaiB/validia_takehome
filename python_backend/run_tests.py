#!/usr/bin/env python3
"""
Test runner script for the fraud detection system.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.stdout:
        print("STDOUT:")
        print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    if result.returncode != 0:
        print(f"❌ {description} failed with return code {result.returncode}")
        return False
    else:
        print(f"✅ {description} completed successfully")
        return True


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Run tests for the fraud detection system")
    parser.add_argument("--type", choices=["unit", "integration", "contract", "all"], 
                       default="all", help="Type of tests to run")
    parser.add_argument("--coverage", action="store_true", help="Run with coverage")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    parser.add_argument("--file", help="Run specific test file")
    
    args = parser.parse_args()
    
    # Change to the project directory
    project_dir = Path(__file__).parent
    import os
    os.chdir(project_dir)
    
    # Base pytest command
    cmd = ["python3", "-m", "pytest"]
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend(["--cov=.", "--cov-report=html", "--cov-report=term-missing"])
    
    # Add verbose flag
    if args.verbose:
        cmd.append("-v")
    
    # Add fast flag to skip slow tests
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    # Add specific test type or file
    if args.file:
        cmd.append(args.file)
    elif args.type == "unit":
        cmd.append("tests/unit/")
    elif args.type == "integration":
        cmd.append("tests/integration/")
    elif args.type == "contract":
        cmd.append("tests/contract/")
    else:  # all
        cmd.append("tests/")
    
    # Run the tests
    success = run_command(cmd, f"Running {args.type} tests")
    
    if success:
        print(f"\n🎉 All {args.type} tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print(f"\n💥 {args.type} tests failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
