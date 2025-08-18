from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from email_validator import validate_email, EmailNotValidError

from src.models.user import User

class LoginForm(FlaskForm):
    """Form for user login"""
    login = StringField('Username or Email', validators=[
        DataRequired(message='Username or email is required'),
        Length(min=3, max=120, message='Username or email must be between 3 and 120 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required')
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    """Form for user registration"""
    username = StringField('Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address'),
        Length(max=120, message='Email must be less than 120 characters')
    ])
    password = PasswordField('Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        """Validate that username is unique"""
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different username.')
    
    def validate_email(self, email):
        """Validate that email is unique and properly formatted"""
        # First validate email format using email-validator
        try:
            validate_email(email.data)
        except EmailNotValidError:
            raise ValidationError('Please enter a valid email address.')
        
        # Then check if email is already in use
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email address.')
    
    def validate_password(self, password):
        """Validate password complexity"""
        pwd = password.data
        
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in pwd):
            raise ValidationError('Password must contain at least one uppercase letter.')
        
        # Check for at least one lowercase letter
        if not any(c.islower() for c in pwd):
            raise ValidationError('Password must contain at least one lowercase letter.')
        
        # Check for at least one digit
        if not any(c.isdigit() for c in pwd):
            raise ValidationError('Password must contain at least one number.')

class PasswordResetRequestForm(FlaskForm):
    """Form for requesting password reset"""
    email = StringField('Email', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address')
    ])
    submit = SubmitField('Request Password Reset')
    
    def validate_email(self, email):
        """Validate that email exists in the system"""
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('No account found with that email address.')

class PasswordResetForm(FlaskForm):
    """Form for resetting password with token"""
    password = PasswordField('New Password', validators=[
        DataRequired(message='Password is required'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your password'),
        EqualTo('password', message='Passwords must match')
    ])
    submit = SubmitField('Reset Password')
    
    def validate_password(self, password):
        """Validate password complexity"""
        pwd = password.data
        
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in pwd):
            raise ValidationError('Password must contain at least one uppercase letter.')
        
        # Check for at least one lowercase letter
        if not any(c.islower() for c in pwd):
            raise ValidationError('Password must contain at least one lowercase letter.')
        
        # Check for at least one digit
        if not any(c.isdigit() for c in pwd):
            raise ValidationError('Password must contain at least one number.')

class ChangePasswordForm(FlaskForm):
    """Form for changing password when logged in"""
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Current password is required')
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(message='New password is required'),
        Length(min=8, message='Password must be at least 8 characters long')
    ])
    confirm_password = PasswordField('Confirm New Password', validators=[
        DataRequired(message='Please confirm your new password'),
        EqualTo('new_password', message='Passwords must match')
    ])
    submit = SubmitField('Change Password')
    
    def validate_new_password(self, new_password):
        """Validate password complexity"""
        pwd = new_password.data
        
        # Check for at least one uppercase letter
        if not any(c.isupper() for c in pwd):
            raise ValidationError('Password must contain at least one uppercase letter.')
        
        # Check for at least one lowercase letter
        if not any(c.islower() for c in pwd):
            raise ValidationError('Password must contain at least one lowercase letter.')
        
        # Check for at least one digit
        if not any(c.isdigit() for c in pwd):
            raise ValidationError('Password must contain at least one number.')
    
    def validate_current_password(self, current_password):
        """Validate that current password is correct"""
        from flask_login import current_user
        from flask import current_app
        from src.auth import get_user_id
        
        # Get current user (handle test mode)
        if current_app.config.get('TESTING', False):
            user_id = get_user_id()
            if user_id:
                test_user = User.query.get(user_id)
                if test_user and not test_user.check_password(current_password.data):
                    raise ValidationError('Current password is incorrect.')
        else:
            if current_user.is_authenticated:
                if not current_user.check_password(current_password.data):
                    raise ValidationError('Current password is incorrect.')

class ChangeUsernameForm(FlaskForm):
    """Form for changing username"""
    new_username = StringField('New Username', validators=[
        DataRequired(message='Username is required'),
        Length(min=3, max=80, message='Username must be between 3 and 80 characters')
    ])
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Current password is required to change username')
    ])
    submit = SubmitField('Change Username')
    
    def validate_new_username(self, new_username):
        """Validate that new username is unique and different from current"""
        from flask_login import current_user
        from flask import current_app
        from src.auth import get_user_id
        
        # Get current user (handle test mode)
        if current_app.config.get('TESTING', False):
            user_id = get_user_id()
            if user_id:
                test_user = User.query.get(user_id)
                if test_user and test_user.username == new_username.data:
                    raise ValidationError('New username must be different from current username.')
        else:
            # Check if username is different from current
            if current_user.is_authenticated and current_user.username == new_username.data:
                raise ValidationError('New username must be different from current username.')
        
        # Check if username is unique
        user = User.query.filter_by(username=new_username.data).first()
        if user:
            raise ValidationError('Username already exists. Please choose a different username.')
    
    def validate_current_password(self, current_password):
        """Validate that current password is correct"""
        from flask_login import current_user
        from flask import current_app
        from src.auth import get_user_id
        
        # Get current user (handle test mode)
        if current_app.config.get('TESTING', False):
            user_id = get_user_id()
            if user_id:
                test_user = User.query.get(user_id)
                if test_user and not test_user.check_password(current_password.data):
                    raise ValidationError('Current password is incorrect.')
        else:
            if current_user.is_authenticated:
                if not current_user.check_password(current_password.data):
                    raise ValidationError('Current password is incorrect.')

class ChangeEmailForm(FlaskForm):
    """Form for changing email address"""
    new_email = StringField('New Email Address', validators=[
        DataRequired(message='Email is required'),
        Email(message='Please enter a valid email address'),
        Length(max=120, message='Email must be less than 120 characters')
    ])
    current_password = PasswordField('Current Password', validators=[
        DataRequired(message='Current password is required to change email')
    ])
    submit = SubmitField('Change Email')
    
    def validate_new_email(self, new_email):
        """Validate that new email is unique, properly formatted, and different from current"""
        from flask_login import current_user
        from flask import current_app
        from src.auth import get_user_id
        
        # First validate email format using email-validator
        try:
            validate_email(new_email.data)
        except EmailNotValidError:
            raise ValidationError('Please enter a valid email address.')
        
        # Get current user (handle test mode)
        if current_app.config.get('TESTING', False):
            user_id = get_user_id()
            if user_id:
                test_user = User.query.get(user_id)
                if test_user and test_user.email == new_email.data:
                    raise ValidationError('New email must be different from current email.')
        else:
            # Check if email is different from current
            if current_user.is_authenticated and current_user.email == new_email.data:
                raise ValidationError('New email must be different from current email.')
        
        # Check if email is unique
        user = User.query.filter_by(email=new_email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email address.')
    
    def validate_current_password(self, current_password):
        """Validate that current password is correct"""
        from flask_login import current_user
        from flask import current_app
        from src.auth import get_user_id
        
        # Get current user (handle test mode)
        if current_app.config.get('TESTING', False):
            user_id = get_user_id()
            if user_id:
                test_user = User.query.get(user_id)
                if test_user and not test_user.check_password(current_password.data):
                    raise ValidationError('Current password is incorrect.')
        else:
            if current_user.is_authenticated:
                if not current_user.check_password(current_password.data):
                    raise ValidationError('Current password is incorrect.')