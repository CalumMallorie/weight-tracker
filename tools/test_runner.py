#!/usr/bin/env python3
"""
Test Runner for Weight Tracker

This script provides an easy way to run different types of tests:
- Fast tests (unit tests, default)
- Integration tests (includes Docker tests)
- All tests (including slow and network tests)

Usage:
    python tools/test_runner.py [OPTIONS]

Examples:
    python tools/test_runner.py                    # Fast tests only
    python tools/test_runner.py --level fast       # Fast tests only  
    python tools/test_runner.py --level integration # Integration tests
    python tools/test_runner.py --level all        # All tests
    python tools/test_runner.py --docker-only      # Only Docker tests
    python tools/test_runner.py --coverage         # With coverage report
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], description: str) -> bool:
    """Run a command and return success status."""
    print(f"\n🔄 {description}")
    print(f"Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=True, cwd=Path(__file__).parent.parent)
        print(f"✅ {description} - SUCCESS")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - FAILED (exit code: {e.returncode})")
        return False
    except FileNotFoundError:
        print(f"❌ {description} - FAILED (command not found)")
        return False


def check_dependencies() -> bool:
    """Check if required dependencies are available."""
    print("🔍 Checking dependencies...")
    
    # Check if pytest is available
    try:
        subprocess.run(['python', '-m', 'pytest', '--version'], 
                      check=True, capture_output=True)
        print("✅ pytest is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ pytest not available. Install with: pip install pytest")
        return False
    
    # Check if Docker is available (optional)
    try:
        subprocess.run(['docker', '--version'], 
                      check=True, capture_output=True)
        print("✅ Docker is available")
        docker_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  Docker not available - Docker tests will be skipped")
        docker_available = False
    
    return True


def main():
    parser = argparse.ArgumentParser(
        description="Run Weight Tracker tests with different configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Test Levels:
  fast         Unit tests only (default, ~10-30 seconds)
  integration  Unit + integration tests (~2-5 minutes)  
  all          All tests including slow/Docker tests (~5-15 minutes)

Examples:
  %(prog)s                          # Fast tests
  %(prog)s --level integration      # Integration tests
  %(prog)s --level all --coverage   # All tests with coverage
  %(prog)s --docker-only            # Docker tests only
        """
    )
    
    parser.add_argument(
        '--level', '-l',
        choices=['fast', 'integration', 'all'],
        default='fast',
        help='Test level to run (default: fast)'
    )
    
    parser.add_argument(
        '--docker-only',
        action='store_true',
        help='Run only Docker tests'
    )
    
    parser.add_argument(
        '--coverage', '-c',
        action='store_true',
        help='Generate coverage report'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    
    parser.add_argument(
        '--failfast', '-x',
        action='store_true',
        help='Stop on first failure'
    )
    
    parser.add_argument(
        '--parallel', '-n',
        type=int,
        help='Run tests in parallel (number of workers)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be run without executing'
    )
    
    args = parser.parse_args()
    
    print("🧪 Weight Tracker Test Runner")
    print("=" * 50)
    
    if not check_dependencies():
        sys.exit(1)
    
    # Build pytest command
    cmd = ['python', '-m', 'pytest']
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend(['--cov=src', '--cov-report=html', '--cov-report=term'])
    
    # Add verbosity
    if args.verbose:
        cmd.append('-vvv')
    else:
        cmd.append('-v')
    
    # Add fail fast
    if args.failfast:
        cmd.append('-x')
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(['-n', str(args.parallel)])
    
    # Determine test selection based on level or docker-only
    if args.docker_only:
        cmd.extend(['-m', 'docker'])
        test_description = "Docker tests only"
        estimated_time = "5-10 minutes"
    elif args.level == 'fast':
        cmd.extend(['-m', 'not (docker or slow or network)'])
        test_description = "Fast tests (unit tests)"
        estimated_time = "10-30 seconds"
    elif args.level == 'integration':
        cmd.extend(['-m', 'not (slow or network) or integration'])
        test_description = "Integration tests (no slow/network tests)"
        estimated_time = "1-3 minutes"
    elif args.level == 'all':
        # Run all tests
        test_description = "All tests (including slow and Docker tests)"
        estimated_time = "5-15 minutes"
    
    print(f"📋 Test Selection: {test_description}")
    print(f"⏱️  Estimated Time: {estimated_time}")
    
    if args.dry_run:
        print(f"\n🔍 Dry run - would execute:")
        print(f"   {' '.join(cmd)}")
        return
    
    print(f"\n🚀 Starting tests...")
    
    # Run the tests
    success = run_command(cmd, f"Running {test_description}")
    
    if success:
        print(f"\n🎉 All tests passed!")
        if args.coverage:
            print("📊 Coverage report generated in htmlcov/index.html")
    else:
        print(f"\n💥 Some tests failed!")
        sys.exit(1)


if __name__ == '__main__':
    main() 