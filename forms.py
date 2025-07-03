from wtforms import Form, StringField, IntegerField, RadioField, SelectField, DateField, DateTimeField, TextAreaField, validators

ACTIVITY_OCCURENCE = [
    ("", "Select"),
    ("I", "Infrequent"),
    ("OM", "Once a Month"),
    ("TM", "Twice a Month"),
    ("W", "Weekly")
]

JOIN_TYPE = [
    ("PU", "Public"),
    ("PR", "Private")
]

CC_LOCATION = [
    ("", "Select"),
    ("O", "Online"),
    ("AL", "Aljunied"),
    ("AN", "Anchorvale"),
    ("AMK", "Ang Mo Kio"),
    ("BE", "Bedok"),
    ("BI", "Bishan"),
    ("BO", "Boon Lay")
]

class InterestGroupProposalForm(Form):
    name = StringField("Group Name", [validators.length(min=1, max=50), validators.DataRequired()])
    topic = StringField("Group Topic", [validators.length(min=1, max=50), validators.DataRequired()])
    description = StringField("Group Description", [validators.length(min=1, max=200), validators.DataRequired()])
    max_size = IntegerField("Maximum Group Size", [validators.NumberRange(min=10, max=100), validators.DataRequired()])
    join_type = RadioField("Group Join Type", [validators.DataRequired()], choices=JOIN_TYPE)
    activity_occurence = SelectField("Activity Occurrence", [validators.DataRequired()], choices=ACTIVITY_OCCURENCE, default="")
    reason = TextAreaField("Proposal Elaboration", [validators.length(min=1, max=1000), validators.DataRequired()])


class ActivityProposalForm(Form):
    name = StringField("Activity Name", [validators.DataRequired(), validators.length(min=1,max=50)])
    description = StringField("Activity Description", [validators.DataRequired(), validators.length(min=1, max=200)])
    start_datetime = DateTimeField("Activity Start Date", [validators.DataRequired()])
    end_datetime = DateTimeField("Activity End Date", [validators.DataRequired()])
    max_size = IntegerField("Max Group Size", [validators.DataRequired(), validators.NumberRange(min=1, max=50)])
    funds = IntegerField("Fund Request", [validators.DataRequired(), validators.NumberRange(min=50, max=1000)])
    location = SelectField("Location", [validators.DataRequired()], choices=CC_LOCATION, default="")
    tags = TextAreaField("Group Tags", [validators.length(min=1, max=300), validators.Optional()])
    remarks = TextAreaField("Additional remarks", [validators.Optional(), validators.length(min=1, max=300)])