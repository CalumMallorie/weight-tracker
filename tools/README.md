# Development Tools

This directory contains helper scripts for developing and running the Weight Tracker app.

## launch_app.py

A convenience script that:
- Starts the Flask app in development mode (debug=True, auto-reload enabled)
- Automatically opens the app in your default browser
- Runs on `http://localhost:8080` by default

### Usage

```bash
# Run from the project root directory
python tools/launch_app.py

# Or make it executable and run directly
chmod +x tools/launch_app.py
./tools/launch_app.py
```

### Features

- **Auto-browser opening**: Automatically opens `http://localhost:8080` in your default browser
- **Development mode**: Debug mode enabled with auto-reload on file changes  
- **Clean output**: Formatted startup messages and graceful shutdown
- **Error handling**: Proper error messages and exit codes
- **Threaded**: Handles multiple requests concurrently

### Environment Variables

- `PORT`: Override the default port (8080)
- `FLASK_DEBUG`: Set to 'false' to disable debug mode (defaults to 'true')

### Requirements

Make sure you have the required dependencies installed:
```bash
pip install -r requirements.txt
```

## test_runner.py

A comprehensive test runner that supports different test levels and configurations for comprehensive testing strategies.

### Features

- **Multiple test levels**: Fast, integration, and full test suites
- **Docker build testing**: Automated Docker image building and container testing
- **Coverage reporting**: HTML and terminal coverage reports
- **Smart dependency checking**: Automatically detects available tools
- **Parallel execution**: Support for running tests in parallel

### Usage

```bash
# Run fast tests only (default, ~10-30 seconds)
python tools/test_runner.py

# Run integration tests (~1-3 minutes)
python tools/test_runner.py --level integration

# Run all tests including Docker tests (~5-15 minutes)  
python tools/test_runner.py --level all

# Run only Docker tests
python tools/test_runner.py --docker-only

# Run with coverage report
python tools/test_runner.py --coverage

# Run with verbose output and fail on first error
python tools/test_runner.py --verbose --failfast

# Show what would be run without executing
python tools/test_runner.py --dry-run
```

### Test Levels

- **fast**: Unit tests only, no external dependencies (~10-30 seconds)
- **integration**: Unit + integration tests, no slow/Docker tests (~1-3 minutes)  
- **all**: All tests including Docker builds and slow tests (~5-15 minutes)

### Test Markers

The test suite uses pytest markers to categorize tests:

- `@pytest.mark.unit`: Fast unit tests (business logic, API)
- `@pytest.mark.integration`: Medium-speed integration tests (UI, templates)
- `@pytest.mark.docker`: Docker-related tests (requires Docker)
- `@pytest.mark.slow`: Long-running tests
- `@pytest.mark.network`: Tests requiring network access

### Direct pytest Commands

You can also run pytest directly with specific markers:

```bash
# Fast tests only
pytest -m "not (docker or slow or network)"

# Docker tests only  
pytest -m docker

# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html --cov-report=term
```

### GitHub Actions Integration

The repository includes automated testing via GitHub Actions:

- **Fast tests**: Run automatically on every push/PR
- **Long tests**: Optional, triggered by:
  - Manual workflow dispatch with "Run long tests" checkbox
  - Commit messages containing `[test-docker]`

### Requirements

- Python 3.11+
- All dependencies from `requirements.txt`  
- Docker (for Docker-related tests)
- pytest and testing dependencies 