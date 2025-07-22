import json
from datetime import datetime, timedelta
import dotenv
from wtforms import Form, StringField, IntegerField, RadioField, SelectField, DateField, DateTimeField, TextAreaField, validators, PasswordField
from flask import current_app
import db

dotenv.load_dotenv()

def get_activity_location():
    connection = db.open_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM activity_location")
    result = cursor.fetchall()
    result.insert(0, ("", "Select"))
    connection.close()
    return result

def get_activity_occurence():
    connection = db.open_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM activity_occurences")
    result = cursor.fetchall()
    result.insert(0, ("", "Select"))
    connection.close()
    return result

JOIN_TYPE = [
    (1, "Public"),
    (0, "Private")
]

def start_datetime_check(form, field: DateTimeField):
    if not isinstance(field.data, datetime):
        raise validators.ValidationError("Invalid date format, please try again.")
    elif field.data < datetime.now():
        raise validators.ValidationError("Start date must be in the future.")
    elif field.data < datetime.now() + timedelta(days=4):
        raise validators.ValidationError("Start date must be at least 4 days from now.")
    elif field.data > datetime.now() + timedelta(days=30):
        raise validators.ValidationError("Start date must be within 30 days from now.")
    return
    
def end_datetime_check(form, field: DateTimeField):
    if not isinstance(form.start_datetime.data, datetime):
        return
    elif not isinstance(field.data, datetime):
        raise validators.ValidationError("Invalid date format, please try again.")
    elif field.data < form.start_datetime.data:
        raise validators.ValidationError("End date must be after the start date.")
    elif (field.data - form.start_datetime.data).total_seconds() / 3600 < 1:
        raise validators.ValidationError("Activity duration must be at least 1 hour.")
    elif field.data > form.start_datetime.data + timedelta(days=5):
        raise validators.ValidationError("End date must be within 5 days from the start date.")
    return

class InterestGroupProposalForm(Form):
    name = StringField("Group Name", [validators.length(min=1, max=50), validators.DataRequired()])
    topic = StringField("Group Topic", [validators.length(min=1, max=50), validators.DataRequired()])
    description = StringField("Group Description", [validators.length(min=1, max=200), validators.DataRequired()])
    max_size = IntegerField("Maximum Group Size", [validators.NumberRange(min=10, max=100), validators.DataRequired()])
    join_type = RadioField("Group Join Type", [validators.DataRequired()], choices=JOIN_TYPE)
    activity_occurence = SelectField("Activity Occurrence", [validators.DataRequired()], choices=get_activity_occurence(), default="")
    reason = TextAreaField("Proposal Elaboration", [validators.length(min=1, max=1000), validators.DataRequired()])


class ActivityProposalForm(Form):
    name = StringField("Activity Name", [validators.DataRequired(), validators.length(min=1,max=50)])
    description = StringField("Activity Description", [validators.DataRequired(), validators.length(min=1, max=200)])
    start_datetime = DateTimeField("Activity Start Date", [validators.DataRequired(message="Invalid value, please try again"), start_datetime_check], format="%Y-%m-%d %H:%M")
    end_datetime = DateTimeField("Activity End Date", [validators.DataRequired(message="Invalid value, please try again"), end_datetime_check], format="%Y-%m-%d %H:%M")
    max_size = IntegerField("Max Group Size", [validators.DataRequired(), validators.NumberRange(min=10, max=50, message="Range must be between 10 and 50")])
    funds = IntegerField("Fund Request", [validators.DataRequired(), validators.NumberRange(min=0, max=1000, message="Range must be between 0 and 1000")])
    location = SelectField("Location", [validators.DataRequired()], choices=get_activity_location(), default="")
    tags = TextAreaField("Group Tags", [validators.length(min=1, max=300), validators.Optional()])
    remarks = TextAreaField("Additional remarks", [validators.Optional(), validators.length(min=1, max=300)])

    def validate_tags(form, field):
        try:
            tags = json.loads(field.data)
            if not isinstance(tags, list):
                raise validators.ValidationError("Incorrect formating of tags")
            for tag in tags:
                if not isinstance(tag, dict) or "value" not in tag:
                    raise validators.ValidationError("Incorrect formating of tags")
        except json.JSONDecodeError:
            raise validators.ValidationError("Invalid formatting of tags")

class LoginForm(Form):
    email = StringField("Email", [
        validators.DataRequired(message="Email is required."),
        validators.Email(message="Please enter a valid email address."),
        validators.Length(max=120)
    ])
    password = PasswordField("Password", [
        
        validators.DataRequired(message="Password is required."),
        validators.Length(min=8, max=128, message="Password must be at least 8 characters.")
    ])

class SignUpForm(Form):
    first_name = StringField("First Name", [
        validators.DataRequired(message="First name is required."),
        validators.Length(min=1, max=50)
    ])
    last_name = StringField("Last Name", [
        validators.DataRequired(message="Last name is required."),
        validators.Length(min=1, max=50)
    ])
    email = StringField("Email", [
        validators.DataRequired(message="Email is required."),
        validators.Email(message="Please enter a valid email address."),
        validators.Length(max=120)
    ])
    password = PasswordField("Password", [
        validators.DataRequired(message="Password is required."),
        validators.Length(min=8, max=128, message="Password must be at least 8 characters.")
    ])
    confirm_password = PasswordField("Confirm Password", [
        validators.DataRequired(message="Please confirm your password."),
        validators.EqualTo('password', message="Passwords must match.")
    ])
    role = SelectField("Role", [
        validators.DataRequired(message="Role is required.")
    ], choices=[('volunteer', 'Volunteer'), ('elderly', 'Elderly')], default="")
