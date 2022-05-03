from flask_wtf import FlaskForm
from wtforms import StringField
from wtforms.validators import DataRequired


class InputForm(FlaskForm):
    input_string = StringField("Enter FEN", validators=[DataRequired()])
