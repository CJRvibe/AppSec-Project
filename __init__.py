import os
from flask import Flask, render_template, redirect, url_for, request, abort
from forms import InterestGroupProposalForm
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template("home.html")

#test data
activities = [
    {
        "id": 1,
        "category": "Music & Vocal",
        "name": "Karaoke",
        "image": "img/karaoke.jpg",
        "desc": "Sing your heart out in a private karaoke room!",
        "timings": "Fridays 7PM - 9PM",
        "min_age": 16,
        "requirements": "Must love music and have noise tolerance. No prior singing experience required!",
    },
    {
        "id": 1,
        "category": "Music & Vocal",
        "name": "Karaoke",
        "image": "img/karaoke.jpg",
        "desc": "Sing your heart out in a private karaoke room!",
        "timings": "Fridays 7PM - 9PM",
        "min_age": 16,
        "requirements": "Must love music and have noise tolerance. No prior singing experience required!",
    },
    {
        "id": 1,
        "category": "Music & Vocal",
        "name": "Karaoke",
        "image": "img/karaoke.jpg",
        "desc": "Sing your heart out in a private karaoke room!",
        "timings": "Fridays 7PM - 9PM",
        "min_age": 16,
        "requirements": "Must love music and have noise tolerance. No prior singing experience required!",
    },
    {
        "id": 1,
        "category": "Music & Vocal",
        "name": "Karaoke",
        "image": "img/karaoke.jpg",
        "desc": "Sing your heart out in a private karaoke room!",
        "timings": "Fridays 7PM - 9PM",
        "min_age": 16,
        "requirements": "Must love music and have noise tolerance. No prior singing experience required!",
    },
]

@app.route('/activityHub')
def activity_hub():
    return render_template('activity_hub.html', activities=activities)

@app.route("/activityView/<int:activity_id>")
def activity_view(activity_id):
    activity = next((a for a in activities if a["id"] == activity_id), None)
    if activity is None:
        abort(404)
    return render_template("activity_view.html", activity=activity)

@app.route("/createInterestGroupProposal", methods=["GET", "POST"])
def create_group_proposal():
    proposal_form = InterestGroupProposalForm(request.form)
    if request.method == "POST" and proposal_form.validate():
        return redirect(url_for("index"))
    return render_template("create_interest_group_proposal.html", form=proposal_form)


if __name__ == "__main__":
    app.run()