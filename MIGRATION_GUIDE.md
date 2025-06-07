# Database Migration Guide

## Overview

This guide documents the migration from test database to production database copy for development and testing.

## Background

Previously, the development environment used a small test database (`instance/weight_tracker.db`) that didn't reflect the production environment complexities. This led to bugs that only manifested in production.

## Migration Process

### 1. Problem Identified
- **Issue**: Body Mass entries were saving as 0kg instead of actual weight in production
- **Root Cause**: Body Mass category had both `is_body_mass=True` AND `is_body_weight=True` 
- **Why Not Caught**: Test database had correct configuration, production database was corrupted

### 2. Solution Implemented
- Copied production database to `user_instance/instance/weight_tracker.db`
- Fixed database corruption: Set `is_body_weight_exercise=False` for Body Mass category
- Renamed `is_body_weight` to `is_body_weight_exercise` for clarity
- Added migration v7 to handle column rename in production

### 3. Migration Steps Performed

```bash
# 1. Backup original test database
cp instance/weight_tracker.db instance/weight_tracker.db.backup

# 2. Replace with production database copy (fixed)
cp user_instance/instance/weight_tracker.db instance/weight_tracker.db

# 3. Clean up redundant directories
rm -rf user_instance/
```

## Post-Migration Verification

1. ✅ All existing tests should pass
2. ✅ Body Mass entries save correct weight values
3. ✅ Category configurations are correct:
   - Body Mass: `is_body_mass=true, is_body_weight_exercise=false`
   - Body Weight Exercises: `is_body_mass=false, is_body_weight_exercise=true`
   - Regular Exercises: `is_body_mass=false, is_body_weight_exercise=false`

## New Test Requirements

The following test scenarios have been added to prevent similar issues:

1. **Database Integrity Tests**: Verify category flags are mutually exclusive
2. **Production Parity Tests**: Ensure test database reflects production structure
3. **Weight Entry Validation Tests**: Test actual weight saving vs. conversion to 0
4. **Migration Regression Tests**: Verify all migrations work on production-like data

## Files Modified

- `instance/weight_tracker.db` - Replaced with production copy
- `src/models.py` - Renamed `is_body_weight` to `is_body_weight_exercise`
- `src/services.py` - Updated all references to new column name
- `src/routes.py` - Updated all references to new column name
- `src/templates/*.html` - Updated all references to new column name
- `src/migration.py` - Added migration v7 for column rename
- `tests/` - Added new regression tests

## Impact

- ✅ Development environment now mirrors production
- ✅ Bugs like the zero weight issue will be caught in testing
- ✅ Database schema is cleaner and more descriptive
- ✅ Migration system handles production deployment automatically 