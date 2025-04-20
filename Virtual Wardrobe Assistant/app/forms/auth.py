from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models.user import User

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8)])
    password2 = PasswordField('Confirm Password', 
                             validators=[DataRequired(), EqualTo('password')])
    location = StringField('Location (City, Country)', validators=[Length(max=100)])
    style_preference = SelectField('Style Preference', 
                                  choices=[
                                      ('', 'Select...'),
                                      ('casual', 'Casual'),
                                      ('formal', 'Formal'),
                                      ('business', 'Business'),
                                      ('sporty', 'Sporty'),
                                      ('minimal', 'Minimalist'),
                                      ('vintage', 'Vintage'),
                                      ('streetwear', 'Streetwear')
                                  ])
    submit = SubmitField('Register')
    
    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user is not None:
            raise ValidationError('Username already taken. Please use a different username.')
    
    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is not None:
            raise ValidationError('Email already registered. Please use a different email address.')

class ProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=64)])
    email = StringField('Email', validators=[DataRequired(), Email(), Length(max=120)])
    password = PasswordField('New Password (leave blank to keep current)', validators=[Length(min=0, max=64)])
    password2 = PasswordField('Confirm New Password', 
                             validators=[EqualTo('password')])
    location = StringField('Location (City, Country)', validators=[Length(max=100)])
    style_preference = SelectField('Style Preference', 
                                  choices=[
                                      ('', 'Select...'),
                                      ('casual', 'Casual'),
                                      ('formal', 'Formal'),
                                      ('business', 'Business'),
                                      ('sporty', 'Sporty'),
                                      ('minimal', 'Minimalist'),
                                      ('vintage', 'Vintage'),
                                      ('streetwear', 'Streetwear')
                                  ])
    submit = SubmitField('Update Profile')
    
    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.original_username = kwargs.get('obj', None).username if kwargs.get('obj', None) else None
        self.original_email = kwargs.get('obj', None).email if kwargs.get('obj', None) else None
    
    def validate_username(self, username):
        if username.data != self.original_username:
            user = User.query.filter_by(username=username.data).first()
            if user is not None:
                raise ValidationError('Username already taken. Please use a different username.')
    
    def validate_email(self, email):
        if email.data != self.original_email:
            user = User.query.filter_by(email=email.data).first()
            if user is not None:
                raise ValidationError('Email already registered. Please use a different email address.') 