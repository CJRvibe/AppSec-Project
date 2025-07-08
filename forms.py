from wtforms import Form, StringField, IntegerField, RadioField, SelectField, DateField, DateTimeField, TextAreaField, validators
from flask import current_app
import db

def get_activity_location():
    connection = db.open_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM activity_location")
    result = cursor.fetchall()
    result.insert(0, ("", "Select"))
    print(result)
    connection.close()
    return result

def get_activity_occurence():
    connection = db.open_db()
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM activity_occurences")
    result = cursor.fetchall()
    result.insert(0, ("", "Select"))
    print(result)
    connection.close()
    return result

JOIN_TYPE = [
    (1, "Public"),
    (2, "Private")
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