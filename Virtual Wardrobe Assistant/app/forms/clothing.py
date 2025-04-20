from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, DateField, FloatField, BooleanField, SelectField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired, Length, Optional, NumberRange

class ClothingItemForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    image = FileField('Image', validators=[
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'Images only!')
    ])
    purchase_date = DateField('Purchase Date', format='%Y-%m-%d', validators=[Optional()])
    brand = StringField('Brand', validators=[Length(max=100)])
    occasion = StringField('Occasion (e.g., casual, formal, work)', validators=[Length(max=100)])
    weather_min_temp = FloatField('Minimum Temperature (°C)', validators=[Optional(), NumberRange(min=-50, max=50)])
    weather_max_temp = FloatField('Maximum Temperature (°C)', validators=[Optional(), NumberRange(min=-50, max=50)])
    is_waterproof = BooleanField('Is Waterproof')
    category_id = SelectField('Category', coerce=int, validators=[DataRequired()])
    color_id = SelectField('Color', coerce=int, validators=[DataRequired()])
    seasons = SelectMultipleField('Seasons', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')

class CategoryForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=50)])
    description = TextAreaField('Description', validators=[Length(max=200)])
    submit = SubmitField('Add Category')

class ColorForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(max=50)])
    hex_code = StringField('Hex Color Code (e.g., #FFFFFF)', validators=[Length(max=7)])
    submit = SubmitField('Add Color')

class WearLogForm(FlaskForm):
    date = DateField('Date Worn', format='%Y-%m-%d', validators=[DataRequired()])
    notes = TextAreaField('Notes', validators=[Length(max=200)])
    weather_condition = StringField('Weather Condition', validators=[Length(max=50)])
    temperature = FloatField('Temperature (°C)', validators=[Optional()])
    submit = SubmitField('Log Wear') 