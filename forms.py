from wtforms import Form, StringField, IntegerField, RadioField, SelectField, DateField, DateTimeField, TextAreaField, validators, PasswordField
from flask import current_app
import db

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
    start_datetime = DateTimeField("Activity Start Date", [validators.DataRequired()], format="%Y-%m-%d %H:%M")
    end_datetime = DateTimeField("Activity End Date", [validators.DataRequired()], format="%Y-%m-%d %H:%M")
    max_size = IntegerField("Max Group Size", [validators.DataRequired(), validators.NumberRange(min=10, max=50)])
    funds = IntegerField("Fund Request", [validators.DataRequired(), validators.NumberRange(min=0, max=1000)])
    location = SelectField("Location", [validators.DataRequired()], choices=get_activity_location(), default="")
    tags = TextAreaField("Group Tags", [validators.length(min=1, max=300), validators.Optional()])
    remarks = TextAreaField("Additional remarks", [validators.Optional(), validators.length(min=1, max=300)])

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
