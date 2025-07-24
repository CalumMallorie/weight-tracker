# Development Workflow Guidelines

## 🚨 CRITICAL: Proper Git Workflow

**NEVER commit directly to the main branch. ALWAYS use feature branches and pull requests.**

### ✅ Correct Workflow

1. **Create feature branch**:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Run tests locally BEFORE committing**:
   ```bash
   python -m pytest tests/ -v
   ```

3. **Commit changes**:
   ```bash
   git add .
   git commit -m "feat: your descriptive commit message"
   ```

4. **Push feature branch**:
   ```bash
   git push -u origin feature/your-feature-name
   ```

5. **Create pull request**:
   ```bash
   gh pr create --title "Your Feature Title" --body "Description of changes"
   ```

6. **Wait for CI to pass** before merging
7. **Merge only after all checks pass**

### ❌ What NOT to Do

- ❌ `git push origin main` (direct push to main)
- ❌ `git commit` without running tests first
- ❌ Merging PRs with failing CI
- ❌ Bypassing branch protection

### 🛡️ Branch Protection Rules

Main branch is protected with:
- ✅ Pull requests required
- ✅ Status checks must pass:
  - Fast Tests
  - Security Scan
  - Build Docker Image (when code changes)
- ✅ Branches must be up to date
- ✅ Administrators included

### 📋 Pre-Commit Checklist

Before ANY commit:
- [ ] All tests pass locally: `python -m pytest tests/`
- [ ] Code follows project conventions
- [ ] No secrets or sensitive data committed
- [ ] Commit message follows format: `type: description`

### 🔧 Development Commands

```bash
# Run tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/ -m "not docker" -v

# Run security tests
python -m pytest tests/ -m security -v

# Check code quality
python -m pytest tests/test_security.py -v
```

### 🚀 Release Process

1. Feature branch → PR → CI passes → Merge
2. Main branch automatically triggers:
   - Full CI pipeline
   - Docker build
   - Security scans
3. Tag releases: `git tag v2.x.x && git push origin v2.x.x`

## 🤖 Automation Safeguards

- **Branch protection**: Prevents direct pushes to main
- **Required CI**: All tests must pass before merge
- **Automated testing**: Runs on every branch push
- **Security scanning**: Runs on every PR

## 📝 Commit Message Format

```
type: short description

Longer description if needed

- List of changes
- More details

🤖 Generated with [Claude Code](https://claude.ai/code)
```

Types: `feat`, `fix`, `docs`, `style`, `refactor`, `test`, `chore`

---

**Remember: If you find yourself typing `git push origin main`, STOP and use a feature branch instead!**