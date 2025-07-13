import os
import mysql.connector
import dotenv
from flask import Flask, render_template, redirect, url_for, request, abort, session, flash
from forms import InterestGroupProposalForm, ActivityProposalForm
import db
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

dotenv.load_dotenv()

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.secret_key = "your_secret_key"  
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.teardown_appcontext(db.close_db)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template("home.html")

@app.route('/signUp', methods=['GET', 'POST'])
def sign_up():
    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        role = request.form.get('role')

        if role == "volunteer":
            user_role = 1
        elif role == "elderly":
            user_role = 2
        else:
            flash("Invalid role.", "danger")
            return render_template('sign_up.html')

        if password != confirm:
            flash('Passwords do not match.', 'danger')
            return render_template('sign_up.html')

        if db.insert_user(first_name, last_name, email, password, user_role):
            return redirect(url_for('login'))  
        else:
            flash('Email already exists or database error.', 'danger')
            return render_template('sign_up.html')
    return render_template('sign_up.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = db.verify_user(email, password)
        if user:
            session['user_id'] = user['user_id']
            session['email'] = user['email']
            flash('Logged in successfully!', 'success')
            return redirect(url_for('explore_groups'))  
        else:
            flash('Invalid credentials.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/forgetPassword')
def forget_password():
    return render_template('forget_password.html')

@app.route('/enterPin')
def enter_pin():
    return render_template('enter_pin.html')

@app.route('/changePassword')
def change_password():
    return render_template('change_password.html')

@app.route('/userProfile')
def user_profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = db.get_user_by_id(user_id)
    return render_template('user_profile.html', user=user)

@app.route('/calendar')
def calendar():
    start_hour = 8
    end_hour = 20
    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    timeslots = [f"{h:02d}:00" for h in range(start_hour, end_hour)]
    
    activities = {
        (1, "09:00"): "Yoga Class",        
        (2, "14:00"): "Medical Checkup",   
        (4, "18:00"): "Cooking Workshop",  
        (5, "10:00"): "Art Therapy",       
    }
    
    week_grid = []
    for hour in timeslots:
        row = []
        for day_index in range(7):
            activity = activities.get((day_index, hour), "")
            row.append(activity)
        week_grid.append(row)
    
    return render_template(
        'calendar.html',
        week_grid=week_grid,
        timeslots=timeslots,
        days=days,
        month_name="July",
        year=2025,
    )



groups = [
    {
        "id": 1,
        "category": "Handicraft",
        "name": "Knitters",
        "description": "Welcome to the knitting club, where we are all knitters",
        "image": "img/elderly.jpg",
        "activities": [
            {"id": 1, "category": "Knitting", "name": "Elephant Knit", "image": "img/elderly.jpg", "min age": 60},
            {"id": 2, "category": "Knitting", "name": "Knit Balls", "image": "img/elderly.jpg"},
        ]
    }, 
    {
        "id": 2,
        "category": "Music & Vocal",
        "name": "Karaoke",
        "image": "img/karaoke.jpg",
        "desc": "Sing your heart out in a private karaoke room!",
        "timings": "Fridays 7PM - 9PM",
        "min_age": 16,
        "requirements": "Must love music and have noise tolerance. No prior singing experience required!",
    }
]

@app.route('/exploreGroups')
def explore_groups():
    return render_template('explore_groups.html', groups=groups)

@app.route('/groupHome/<int:group_id>')
def group_home(group_id):
    view = request.args.get('view', 'activities')
    group = next((g for g in groups if g["id"] == group_id), None)
    if group is None:
        abort(404)
    return render_template("group_home.html", group=group, view=view)

@app.route('/group/<int:group_id>/activity/<int:activity_id>')
def view_group_activity(group_id, activity_id):
    group = next((g for g in groups if g["id"] == group_id), None)
    if group is None:
        abort(404)

    activity = next((a for a in group.get("activities", []) if a["id"] == activity_id), None)
    if activity is None:
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