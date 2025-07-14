import os
import mysql.connector
import dotenv
from flask import Flask, render_template, redirect, url_for, request, abort
from forms import InterestGroupProposalForm, ActivityProposalForm
import db
from werkzeug.utils import secure_filename

dotenv.load_dotenv()

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.teardown_appcontext(db.close_db)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    #test
    activity = db.get_interest_activity(1)
    print(activity)
    return render_template("home.html")

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signUp')
def register():
    return render_template('sign_up.html')

@app.route('/forgetPassword')
def forget_password():
    return render_template('forget_password.html')

@app.route('/enterPin')
def enter_pin():
    return render_template('enter_pin.html')

@app.route('/changePassword')
def change_password():
    return render_template('change_password.html')


@app.route('/exploreGroups')
def explore_groups():
    groups = db.get_all_groups()
    print(groups)
    return render_template('explore_groups.html', groups=groups)

@app.route('/groupHome/<int:group_id>')
def group_home(group_id):
    view = request.args.get('view', 'activities')

    group = db.get_group_by_id(group_id)
    if not group:
        abort(404)

    print(group_id)

    activities = db.get_activities_by_group_id(group_id)
    print(activities)
    group["activities"] = activities
    print(group)
    return render_template("group_home.html", group=group, view=view, activities=activities)


@app.route('/group/<int:group_id>/activity/<int:activity_id>')
def view_group_activity(group_id, activity_id):
    group = db.get_group_by_id(group_id)
    if not group:
        abort(404)

    activity = db.get_activity_by_id(activity_id)
    if not activity or activity['group_id'] != group_id:
        abort(404)

    return render_template('activity.html', activity=activity, group=group)
@app.route("/createInterestGroupProposal", methods=["GET", "POST"])
def create_group_proposal():
    proposal_form = InterestGroupProposalForm(request.form)
    if request.method == "POST" and proposal_form.validate():
        return redirect(url_for("index"))
    return render_template("create_interest_group_proposal.html", form=proposal_form)


@app.route("/createInterestGroupActivityProposal", methods=["GET", "POST"])
def create_activity_proposal():
    proposal_form = ActivityProposalForm(request.form)
    if request.method == "POST" and proposal_form.validate():
        return redirect(url_for("index"))
    return render_template("create_group_activity.html", form=proposal_form)


@app.route("/test-discussion")
def discussion_forum():
    return render_template("group_discussion.html")


if __name__ == "__main__":
    app.run()