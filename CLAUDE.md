# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚨 CRITICAL SECURITY RULES - NO EXCEPTIONS

### **ABSOLUTE PROHIBITIONS**
1. **NEVER merge pull requests** using `gh pr merge` or any CLI/API command
2. **NEVER use `git push origin main`** - direct pushes to main are blocked
3. **NEVER bypass branch protection** or workflow safeguards
4. **NEVER commit directly to main branch**

### **REQUIRED WORKFLOW - ALWAYS FOLLOW**
1. **Create feature branches** for ALL changes: `git checkout -b feature/descriptive-name`
2. **Run tests locally** before pushing: `python -m pytest tests/ -v`
3. **Push feature branch**: `git push -u origin feature/branch-name`
4. **Create PR only**: `gh pr create --title "Title" --body "Description"`
5. **STOP HERE** - Let human review and merge via GitHub web interface

### **SUCCESS METRICS**
- **95 tests passing, 7 skipped** (expected result)
- **All CI checks green** before PR creation
- **No direct main branch commits**
- **All changes via PR workflow**

**YOUR JOB ENDS AT PR CREATION. NEVER MERGE. HUMAN MAINTAINS FINAL CONTROL.**

## Development Commands

### Testing
- **Fast tests** (unit tests, ~10-30 seconds): `python tools/test_runner.py` or `pytest -m "not (docker or slow or network)"`
- **Integration tests** (~1-3 minutes): `python tools/test_runner.py --level integration`
- **All tests** including Docker (~5-15 minutes): `python tools/test_runner.py --level all`
- **Docker tests only**: `python tools/test_runner.py --docker-only` or `pytest -m docker`
- **With coverage**: `python tools/test_runner.py --coverage`
- **Single test file**: `pytest tests/test_specific.py`

### Running the Application
- **Development mode**: `python tools/launch_app.py` (auto-opens browser at localhost:8080)
- **Production mode**: `python main.py`
- **Docker**: `docker-compose up --build`

### Database Operations
- Database migrations run automatically on app start
- Database file: `instance/weight_tracker.db` (SQLite)
- Backup location: `data/backup/`

## Architecture Overview

### Core Structure
- **Flask application factory pattern** in `src/app.py` with `create_app()`
- **SQLAlchemy models** in `src/models.py` with database relationships
- **Service layer** in `src/services.py` for business logic and data operations
- **API routes** in `src/routes.py` with separate blueprints for views (`main`) and API endpoints (`api`)
- **Automatic database migrations** in `src/migration.py` that run on startup

### Data Model
The application tracks weight entries across different categories:
- **WeightCategory**: Exercise categories with special flags:
  - `is_body_mass=True`: Body weight tracking (weight only, no reps)
  - `is_body_weight_exercise=True`: Bodyweight exercises (reps only, no weight)
  - Regular exercises: Both weight and reps
- **WeightEntry**: Individual weight/exercise entries with category relationships

### Key Components
- **PWA functionality**: Service worker and manifest in `src/static/`
- **Plotly visualizations**: Charts generated server-side in `services.py`
- **Docker deployment**: Single container with volume mounts for data persistence
- **Comprehensive test suite**: Unit, integration, and Docker tests with pytest markers

### Database Integrity
- **Migration system**: Automatic schema updates on startup
- **Data validation**: Triggers prevent category flag corruption
- **Production parity**: Development uses production database copy to catch environment-specific bugs

### Testing Strategy
- Tests are categorized with pytest markers: `unit`, `integration`, `docker`, `slow`, `network`
- Production database copy used in development to ensure environment parity
- Regression tests prevent category corruption bugs that caused zero weight saves

### Deployment
- Designed for UnRAID/Docker environments
- Persistent volumes: `./data`, `./logs`, `./instance`
- Health checks and auto-restart capabilities
- Port 8080 default with configurable environment variables

## Git Workflow and CI Pipeline

### Commit Practices
- **Commit frequently**: Make regular commits as you complete features or fix bugs
- **Use descriptive commit messages**: Follow the existing style (see recent commits with `git log --oneline -10`)
- **Run tests before committing**: Always run `python tools/test_runner.py` before committing
- **Check git status**: Use `git status` and `git diff` to review changes before committing

### CI Pipeline Awareness
The repository has an optimized GitHub Actions pipeline that ensures quality and security:

#### Automated Testing (Required for Merge)
- **Fast tests**: Run automatically on every PR (~2-3 minutes)
  - Unit tests, API tests, security tests
  - Uses pip caching for speed
  - Must pass to merge
- **Security scanning**: Runs in parallel with tests
  - Dependency vulnerability scanning with `safety`
  - Static code analysis with `bandit`
  - Security-focused test suite
- **Comprehensive tests**: Triggered by:
  - Manual workflow dispatch with "Run long tests" checkbox
  - Commit messages containing `[test-docker]`
  - Pushes to main branch
  - Include Docker builds and integration tests (~5-15 minutes)

#### Automated Docker Building (Smart Conditional)
- **Conditional builds**: Only builds when code changes detected
- **Platform optimization**: 
  - PRs: `linux/amd64` only (faster feedback)
  - Main branch: `linux/amd64,linux/arm64` (full compatibility)
- **Docker Hub publishing**: Pushes to `calomal/weight-tracker` on main branch
- **Caching**: GitHub Actions cache for faster builds

#### Branch Protection (ENFORCED)
- **No direct pushes** to main branch allowed
- **Required status checks**: Fast Tests, Security Scan, Build Docker Image
- **PR requirement**: All changes must go through pull requests
- **Admin enforcement**: Even administrators must follow these rules

### Triggering Long Tests
Add `[test-docker]` to your commit message to run comprehensive tests including Docker builds:
```bash
git commit -m "Add new feature [test-docker]"
```

### Pre-commit Checklist
1. Run fast tests: `python tools/test_runner.py`
2. Check that changes work with Docker: `docker-compose up --build` (optional)
3. Review changes: `git status` and `git diff`
4. Commit with descriptive message
5. CI pipeline will automatically test and build Docker images

## 🔧 SAFE WORKFLOW PATTERNS

### **Standard Feature Development**
```bash
# ALWAYS start with feature branch
git checkout -b feature/your-feature-name

# Make changes, then test
python -m pytest tests/ -v  # Must show: 95 passed, 7 skipped

# Stage and commit with proper format
git add .
git commit -m "feat: descriptive message

🤖 Generated with [Claude Code](https://claude.ai/code)

Co-Authored-By: Claude <noreply@anthropic.com>"

# Push feature branch (pre-push hook runs tests automatically)
git push -u origin feature/your-feature-name

# Create PR - DO NOT MERGE
gh pr create --title "Feature: Your Feature" --body "Description of changes"
```

### **Bug Fix Pattern**
```bash
git checkout -b fix/issue-description
# Fix the issue
python -m pytest tests/ -v  # Verify fix doesn't break anything
git add . && git commit -m "fix: resolve issue description"
git push -u origin fix/issue-description
gh pr create --title "Fix: Issue Description" --body "Details of fix"
```

### **Repository Cleanup**
```bash
# Check branch status
git branch -a
git status

# View CI status (but never merge)
gh pr checks <pr-number>
gh run list --limit 5
```

## ⚠️ ERROR RECOVERY

### **If Tests Fail**
```bash
# Fix the failing tests, then:
python -m pytest tests/ -v
git add . && git commit -m "fix: resolve test failures"
git push  # Pre-push hook will validate again
```

### **If Branch Protection Blocks Push**
```bash
# This is EXPECTED - verify you're on feature branch
git branch  # Should show: * feature/branch-name
# If accidentally on main, create feature branch:
git checkout -b feature/your-fix
```

### **If Pre-push Hook Fails**
```bash
# Tests must pass before any push - this is enforced
# Fix the issues, then retry push
python -m pytest tests/ -v
# Address any failures, then:
git push
```

## 🛡️ SECURITY SAFEGUARDS IN PLACE

### **Automated Protections**
- **Pre-push hook**: Prevents direct pushes to main, runs tests automatically
- **Branch protection**: Requires PRs, status checks, human reviews
- **CI validation**: Fast tests, security scans, comprehensive tests
- **Required status checks**: All tests must pass before merge eligibility

### **Manual Control Points**
- **Human approval**: All PRs require manual review and web merge
- **Security validation**: Human verifies changes before production
- **No CLI bypass**: API/command-line merges are completely blocked