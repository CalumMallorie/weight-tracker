# Weight Tracker Test Instance

A **separated test instance** of the Weight Tracker webapp for development and testing.

## Purpose

This test instance provides:
- **Isolated testing environment** - separate from main application
- **Different port** (8081 vs 8080) - run alongside main app
- **Separate database** - won't interfere with main data
- **Separate logs** - clean test logging
- **Same codebase** - uses actual Weight Tracker code

## Structure

```
test_instance/
├── instance/
│   └── weight_tracker_test.db    # Test database (SQLite)
├── logs/
│   └── test_app.log              # Test instance logs
├── test_config.py                # Test-specific configuration
├── start_test_instance.py        # Launcher script
└── README.md                     # This file
```

## Quick Start

### Start Test Instance

```bash
cd test_instance
python start_test_instance.py
```

### Access Test Instance

- **Test instance URL**: http://127.0.0.1:8081
- **Main app URL**: http://127.0.0.1:8080 (if running)

## Configuration Differences

| Setting | Main App | Test Instance |
|---------|----------|---------------|
| Port | 8080 | 8081 |
| Database | `instance/weight_tracker.db` | `test_instance/instance/weight_tracker_test.db` |
| Logs | `logs/weight_tracker.log` | `test_instance/logs/test_app.log` |
| Debug Mode | Production settings | Always True |
| Environment | Production | TEST_INSTANCE |

## Benefits

### ✅ **Complete Separation**
- Different port - won't conflict with main app
- Separate database - test data isolated
- Separate logs - clean debugging
- Independent configuration

### ✅ **Real Application**
- Uses actual Weight Tracker codebase
- All features available for testing
- Same templates, routes, and logic
- Real database schema and migrations

### ✅ **Realistic Dummy Data**
- Pre-populated with 3 months of exercise data
- Multiple exercise categories (strength, bodyweight, body mass)
- Realistic progression patterns and variations
- Perfect for testing charts and analytics

### ✅ **Development Friendly**
- Debug mode enabled
- Detailed logging
- Auto-reload on code changes
- Easy to start/stop

## Use Cases

1. **Feature Testing** - Test new features without affecting main data
2. **Bug Reproduction** - Isolate issues in clean environment
3. **Development** - Work on changes with live preview
4. **Training Data** - Create test data without cluttering main app
5. **Parallel Testing** - Run tests while main app serves users

## Database

The test instance creates its own SQLite database with:
- Same schema as main app
- Automatic migrations
- Pre-populated with realistic dummy data (3 months of exercise records)
- Isolated from main application data

### Dummy Data Includes:
- **Body Weight**: Daily weight tracking with realistic trends
- **Strength Exercises**: Bench Press, Squat, Deadlift, Overhead Press, Bicep Curls
- **Bodyweight Exercises**: Push-ups, Pull-ups, Plank Hold
- **Realistic Progressions**: Weight increases, rep variations, rest days
- **Time Span**: 90 days of historical data

## Stopping the Test Instance

Press `Ctrl+C` in the terminal where the test instance is running.

## Notes

- Test instance automatically creates required directories
- Database and migrations run automatically on first start
- All Weight Tracker features are available
- Changes to main codebase are reflected in test instance (with auto-reload)