from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateField, FloatField, BooleanField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class OutfitForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    occasion = StringField('Occasion (e.g., casual, formal, work)', validators=[Length(max=100)])
    season = StringField('Season (e.g., summer, winter)', validators=[Length(max=50)])
    weather_min_temp = FloatField('Minimum Temperature (°C)', validators=[Optional(), NumberRange(min=-50, max=50)])
    weather_max_temp = FloatField('Maximum Temperature (°C)', validators=[Optional(), NumberRange(min=-50, max=50)])
    is_favorite = BooleanField('Mark as Favorite')
    submit = SubmitField('Save Outfit')

class WearOutfitForm(FlaskForm):
    date = DateField('Date Worn', format='%Y-%m-%d', validators=[DataRequired()])
    notes = TextAreaField('Notes (occasion, comfort, etc.)', validators=[Length(max=200)])
    weather_condition = StringField('Weather Condition', validators=[Length(max=50)])
    temperature = FloatField('Temperature (°C)', validators=[Optional()])
    submit = SubmitField('Log Wear') 