from wtforms import Form, StringField, IntegerField, RadioField, SelectField, TextAreaField, validators

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

class InterestGroupProposalForm(Form):
    name = StringField("Group Name", [validators.length(min=1, max=100), validators.DataRequired()])
    topic = StringField("Group Topic", [validators.length(min=1, max=100), validators.DataRequired()])
    description = StringField("Group Description", [validators.length(min=1, max=100), validators.DataRequired()])
    activity_occurence = SelectField("Activity Occurrence", [validators.DataRequired()], choices=ACTIVITY_OCCURENCE, default="")
    max_size = IntegerField("Maximum Group Size", [validators.NumberRange(min=10, max=50), validators.DataRequired()])
    join_type = RadioField("Group Join Type", [validators.DataRequired()], choices=JOIN_TYPE)
    reason = TextAreaField("Proposal Elaboration", [validators.length(min=1, max=1000), validators.DataRequired()])
    tags = TextAreaField("Group Tags", [validators.length(min=1, max=300), validators.Optional()])