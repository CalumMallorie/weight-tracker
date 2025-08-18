from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_user, logout_user, current_user
from datetime import datetime, UTC

from src.models import db
from src.models.user import User
from src.forms import LoginForm, RegistrationForm, PasswordResetRequestForm, PasswordResetForm, ChangePasswordForm, ChangeUsernameForm, ChangeEmailForm
from src.auth import anonymous_required, login_required

# Create authentication blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
@anonymous_required
def login():
    """User login page and processing"""
    form = LoginForm()
    
    if form.validate_on_submit():
        # Find user by username or email
        user = User.find_by_username_or_email(form.login.data)
        
        if user and user.check_password(form.password.data) and user.is_active:
            # Log the user in
            login_user(user, remember=form.remember_me.data)
            
            # Update last login timestamp
            user.update_last_login()
            db.session.commit()
            
            # Get next page or redirect to index
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('main.index')
            
            flash(f'Welcome back, {user.username}!', 'success')
            return redirect(next_page)
        else:
            if user and not user.is_active:
                flash('Your account has been deactivated. Please contact support.', 'error')
            else:
                flash('Invalid username/email or password.', 'error')
    
    return render_template('auth/login.html', form=form, title='Sign In')

@auth_bp.route('/register', methods=['GET', 'POST'])
@anonymous_required
def register():
    """User registration page and processing"""
    form = RegistrationForm()
    
    if form.validate_on_submit():
        try:
            # Create new user
            user = User(
                username=form.username.data,
                email=form.email.data
            )
            user.set_password(form.password.data)
            
            # Add to database
            db.session.add(user)
            db.session.commit()
            
            # Create default "Body Mass" category for the new user
            from src.models import WeightCategory
            body_mass_category = WeightCategory(
                name='Body Mass',
                is_body_mass=True,
                is_body_weight_exercise=False,
                user_id=user.id,
                created_at=datetime.now(UTC)
            )
            db.session.add(body_mass_category)
            db.session.commit()
            
            flash(f'Registration successful! Welcome {user.username}!', 'success')
            
            # Automatically log in the new user
            login_user(user)
            user.update_last_login()
            db.session.commit()
            
            return redirect(url_for('main.index'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Registration error: {str(e)}')
            flash('Registration failed. Please try again.', 'error')
    
    return render_template('auth/register.html', form=form, title='Register')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    username = current_user.username if current_user.is_authenticated else 'User'
    logout_user()
    flash(f'Goodbye, {username}!', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/reset-password', methods=['GET', 'POST'])
@anonymous_required
def reset_password_request():
    """Request password reset"""
    form = PasswordResetRequestForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.is_active:
            # Generate reset token
            token = user.generate_reset_token()
            db.session.commit()
            
            # In a real application, you would send an email here
            # For now, we'll just show the token (NOT SECURE - just for development)
            if current_app.config.get('DEVELOPMENT', False):
                flash(f'Password reset requested. Reset token: {token} (Development mode only)', 'info')
                flash(f'Use this link: {url_for("auth.reset_password", token=token, _external=True)}', 'info')
            else:
                flash('If an account with that email exists, a password reset link has been sent.', 'info')
            
            return redirect(url_for('auth.login'))
        else:
            # Don't reveal whether the email exists or not
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/reset_password_request.html', form=form, title='Reset Password')

@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@anonymous_required
def reset_password(token):
    """Reset password with token"""
    # Find user by reset token
    user = User.query.filter_by(reset_token=token).first()
    
    if not user or not user.verify_reset_token(token):
        flash('Invalid or expired reset token.', 'error')
        return redirect(url_for('auth.reset_password_request'))
    
    form = PasswordResetForm()
    
    if form.validate_on_submit():
        try:
            # Update password
            user.set_password(form.password.data)
            user.clear_reset_token()
            db.session.commit()
            
            flash('Your password has been reset successfully!', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Password reset error: {str(e)}')
            flash('Password reset failed. Please try again.', 'error')
    
    return render_template('auth/reset_password.html', form=form, title='Reset Password')

@auth_bp.route('/profile')
@login_required
def profile():
    """User profile page"""
    stats = current_user.get_stats()
    return render_template('auth/profile.html', user=current_user, stats=stats, title='Profile')

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Change password when logged in"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        try:
            # Update password
            current_user.set_password(form.new_password.data)
            db.session.commit()
            
            flash('Your password has been changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Password change error: {str(e)}')
            flash('Password change failed. Please try again.', 'error')
    
    return render_template('auth/change_password.html', form=form, title='Change Password')

@auth_bp.route('/change-username', methods=['GET', 'POST'])
@login_required
def change_username():
    """Change username when logged in"""
    form = ChangeUsernameForm()
    
    if form.validate_on_submit():
        try:
            # Update the username
            current_user.username = form.new_username.data
            current_user.updated_at = datetime.now(UTC)
            
            db.session.commit()
            
            flash('Your username has been changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Username change error: {str(e)}')
            flash('Username change failed. Please try again.', 'error')
    
    return render_template('auth/change_username.html', form=form, title='Change Username')

@auth_bp.route('/change-email', methods=['GET', 'POST'])
@login_required
def change_email():
    """Change email address when logged in"""
    form = ChangeEmailForm()
    
    if form.validate_on_submit():
        try:
            # Update the email
            current_user.email = form.new_email.data
            current_user.updated_at = datetime.now(UTC)
            
            db.session.commit()
            
            flash('Your email address has been changed successfully!', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f'Email change error: {str(e)}')
            flash('Email change failed. Please try again.', 'error')
    
    return render_template('auth/change_email.html', form=form, title='Change Email')

@auth_bp.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Delete user account (requires confirmation)"""
    try:
        user_id = current_user.id
        username = current_user.username
        
        # Log out the user first
        logout_user()
        
        # Delete user and all associated data (cascading deletes will handle entries and categories)
        user = User.query.get(user_id)
        if user:
            db.session.delete(user)
            db.session.commit()
            
            flash(f'Account "{username}" has been deleted successfully.', 'info')
        else:
            flash('Account not found.', 'error')
            
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Account deletion error: {str(e)}')
        flash('Account deletion failed. Please try again.', 'error')
    
    return redirect(url_for('auth.register'))

# Error handlers for auth blueprint
@auth_bp.errorhandler(404)
def not_found_error(error):
    """Handle 404 errors in auth blueprint"""
    return render_template('auth/error.html', 
                         error_code=404, 
                         error_message='Page not found'), 404

@auth_bp.errorhandler(500)
def internal_error(error):
    """Handle 500 errors in auth blueprint"""
    db.session.rollback()
    return render_template('auth/error.html', 
                         error_code=500, 
                         error_message='Internal server error'), 500