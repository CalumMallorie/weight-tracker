# Multi-User Support Implementation Orchestration for Weight Tracker

## Overview
This document provides step-by-step instructions for implementing multi-user support in the Weight Tracker application. Follow these tasks in order, testing after each major section.

## Phase 1: Database Schema Updates

### 1.1 Create User Model
- [ ] Create `src/models/user.py` with User model
  - Fields: id, username (unique), email (unique), password_hash, created_at, updated_at, is_active, last_login
  - Add password hashing methods using werkzeug.security
  - Add authentication helper methods (verify_password, etc.)
  - Add relationship to WeightEntry and WeightCategory

### 1.2 Update Existing Models
- [ ] Modify `src/models.py`:
  - Add `user_id` foreign key to WeightEntry model
  - Add `user_id` foreign key to WeightCategory model
  - Update relationships to include User backref
  - Ensure all queries filter by user_id

### 1.3 Create Database Migration
- [ ] Create migration script in `src/migration.py`:
  - Add migration_v9() function to add user table
  - Add migration_v10() function to add user_id columns to existing tables
  - Create default user for existing data (username: 'default', email: 'default@example.com')
  - Assign all existing entries and categories to default user
  - Update MIGRATIONS list
  - Immediately test the database migration using a dummy database. Do full integration test after this.

## Phase 2: Authentication System

### 2.1 Install Required Dependencies
- [ ] Update `requirements.txt`:
  - Add Flask-Login==0.6.3
  - Add Flask-WTF==1.2.1
  - Add WTForms==3.1.1
  - Add email-validator==2.1.0
  - Add Flask-Bcrypt==1.0.1

### 2.2 Create Authentication Module
- [ ] Create `src/auth.py`:
  - Set up Flask-Login configuration
  - Create login_manager instance
  - Implement user_loader callback
  - Add login_required decorator wrapper

### 2.3 Create Authentication Forms
- [ ] Create `src/forms.py`:
  - LoginForm (username/email, password, remember_me)
  - RegistrationForm (username, email, password, confirm_password)
  - PasswordResetRequestForm (email)
  - PasswordResetForm (password, confirm_password)

### 2.4 Create Authentication Routes
- [ ] Create `src/auth_routes.py`:
  - GET/POST /login - Login page and processing
  - GET/POST /register - Registration page and processing
  - GET /logout - Logout functionality
  - GET/POST /reset-password - Password reset request
  - GET/POST /reset-password/<token> - Password reset with token

### 2.5 Create Authentication Templates
- [ ] Create `src/templates/auth/` directory
- [ ] Create `src/templates/auth/login.html`
- [ ] Create `src/templates/auth/register.html`
- [ ] Create `src/templates/auth/reset_password_request.html`
- [ ] Create `src/templates/auth/reset_password.html`
- [ ] Create `src/templates/auth/base.html` for auth pages layout

## Phase 3: Update Application Logic

### 3.1 Update App Factory
- [ ] Modify `src/app.py`:
  - Initialize Flask-Login
  - Register authentication blueprint
  - Add login manager configuration
  - Set up CSRF protection
  - Configure session security

### 3.2 Update Services Layer
- [ ] Modify `src/services.py`:
  - Add user_id parameter to all data retrieval functions
  - Update save_weight_entry() to include user_id
  - Update get_all_entries() to filter by user_id
  - Update get_all_categories() to filter by user_id
  - Update get_entries_by_time_window() to filter by user_id
  - Add user-specific category creation
  - Ensure Body Mass category is created per user

### 3.3 Update Routes
- [ ] Modify `src/routes.py`:
  - Add @login_required to all routes
  - Pass current_user.id to all service calls
  - Update form handling to include user context
  - Add user-specific redirects after login

### 3.4 Update API Routes
- [ ] Modify API endpoints in `src/routes.py`:
  - Add authentication checks to all API endpoints
  - Return 401 for unauthenticated requests
  - Filter all data by current_user.id
  - Add user context to all operations

## Phase 4: UI Updates

### 4.1 Update Base Template
- [ ] Modify `src/templates/index.html`:
  - Add login/logout links in navigation
  - Show current username when logged in
  - Add "Account" or "Profile" link

### 4.2 Create User Profile Page
- [ ] Create `src/templates/profile.html`:
  - Display user information
  - Show user statistics (total entries, categories, etc.)
  - Add option to change password
  - Add option to download user data

### 4.3 Update All Existing Templates
- [ ] Update `src/templates/entries.html` - Add user context
- [ ] Update `src/templates/categories.html` - Add user context
- [ ] Ensure all templates handle non-authenticated state

## Phase 5: Security Enhancements

### 5.1 Session Security
- [ ] Configure secure session cookies
- [ ] Set session timeout
- [ ] Implement remember me functionality
- [ ] Add CSRF protection to all forms

### 5.2 Password Security
- [ ] Implement password complexity requirements
- [ ] Add password reset token generation
- [ ] Set token expiration (e.g., 1 hour)
- [ ] Rate limit login attempts

### 5.3 Data Access Security
- [ ] Create decorator for user data access validation
- [ ] Ensure no data leakage between users
- [ ] Add logging for security events
- [ ] Implement account lockout after failed attempts

## Phase 6: Testing Updates

### 6.1 Update Test Fixtures
- [ ] Modify `tests/conftest.py`:
  - Add authenticated_client fixture
  - Add test user creation fixtures
  - Add multi-user data fixtures
  - Update app fixture for authentication

### 6.2 Create Authentication Tests
- [ ] Create `tests/test_auth.py`:
  - Test user registration
  - Test login/logout
  - Test password reset
  - Test invalid credentials
  - Test session timeout

### 6.3 Update Existing Tests
- [ ] Update `tests/test_api.py` - Add authentication to API tests
- [ ] Update `tests/test_services.py` - Add user context
- [ ] Update `tests/test_ui.py` - Add login steps
- [ ] Update `tests/test_database_integrity.py` - Test user isolation
- [ ] Update `tests/test_security.py` - Add multi-user security tests

## Phase 7: Migration and Deployment

### 7.1 Create Migration Guide
- [ ] Create `MIGRATION_GUIDE.md`:
  - Instructions for existing users
  - Default user credentials
  - Data migration steps
  - Rollback procedures

### 7.2 Update Docker Configuration
- [ ] Update `docker-compose.yml`:
  - Add environment variables for auth
  - Update health check to handle auth
  - Add volume for sessions if using file-based

### 7.3 Update Documentation
- [ ] Update `README.md` with multi-user information
- [ ] Add authentication setup instructions
- [ ] Document environment variables
- [ ] Add troubleshooting section

## Phase 8: Optional Enhancements

### 8.1 Social Features (Optional)
- [ ] Add ability to share progress (opt-in)
- [ ] Create public profile pages
- [ ] Add achievement system
- [ ] Implement follow/unfollow functionality

### 8.2 Admin Features (Optional)
- [ ] Create admin role in User model
- [ ] Add admin dashboard at /admin
- [ ] User management interface
- [ ] System statistics view

### 8.3 Data Import/Export (Optional)
- [ ] Add CSV export for user data
- [ ] Add CSV import with validation
- [ ] Create data portability API
- [ ] Add scheduled backups per user

## Testing Checklist

After each phase, verify:
- [ ] Existing single-user functionality still works
- [ ] No data leakage between users
- [ ] Authentication is properly enforced
- [ ] UI shows appropriate user context
- [ ] API endpoints respect authentication
- [ ] Database migrations work on existing data
- [ ] Docker build still succeeds
- [ ] All tests pass

## Critical Considerations

1. **Backward Compatibility**: Ensure existing deployments can migrate smoothly
2. **Default User**: All existing data should be assigned to a default user
3. **Session Management**: Use secure session configuration
4. **Password Policy**: Implement reasonable password requirements
5. **Rate Limiting**: Protect against brute force attacks
6. **Data Isolation**: Ensure complete separation of user data
7. **Performance**: Add database indexes for user_id columns
8. **Audit Trail**: Log security-relevant events

## Implementation Order

1. Start with database schema (Phase 1)
2. Implement basic authentication (Phase 2)
3. Update application logic (Phase 3)
4. Update UI (Phase 4)
5. Add security features (Phase 5)
6. Update tests (Phase 6)
7. Prepare for deployment (Phase 7)
8. Consider optional features (Phase 8)

## Notes for Claude Code

- Test each phase thoroughly before moving to the next
- Create backup branches before major changes
- Run the test suite after each significant change
- Pay special attention to data migration for existing users
- Ensure all user-facing errors are helpful and secure
- Document any assumptions or decisions made during implementation