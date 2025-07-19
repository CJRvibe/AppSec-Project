import dotenv
import json
import os
from flask import Flask, render_template, redirect, url_for, request, abort, session, flash
from flask_mail import Mail, Message, Attachment
from forms import *
import db
import config
import admin
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from access_control import login_required, role_required
from authlib.integrations.flask_client import OAuth

dotenv.load_dotenv()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config.from_object(config.DevelopmentConfig)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["MAIL_PASSWORD"] = os.environ["MAIL_PASSWORD"]
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id=app.config["GOOGLE_CLIENT_ID"],
    client_secret=app.config["GOOGLE_CLIENT_SECRET"],
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile'
    }
)

mail = Mail(app)

app.register_blueprint(admin.admin, url_prefix="/admin")
app.teardown_appcontext(db.close_db)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def send_email(recipient, subject, body):
    msg = Message(f"{subject}", recipients=[f'{recipient}'])
    msg.body = f"{body}"
    mail.send(msg)

@app.route('/')
def index():
    return render_template("home.html")

@app.route('/signUp', methods=['GET', 'POST'])
def sign_up():
    form = SignUpForm(request.form)
    if request.method == 'POST' and form.validate():
        first_name = form.first_name.data
        last_name = form.last_name.data
        email = form.email.data
        password = form.password.data
        password = db.hashed_pw(password)
        confirm_password = form.confirm_password.data
        role = form.role.data

        if role == "volunteer":
            user_role = 1
        elif role == "elderly":
            user_role = 2
        elif role == "admin":
            user_role = 3
        else:
            flash("Invalid role.", "danger")
            return render_template('sign_up.html')

        if db.insert_user(first_name, last_name, email, password, user_role):
            flash('User created successfully!', 'success')
            return redirect(url_for('login'))  
        
        elif password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('sign_up.html')
        
        else:
            flash('Email already exists or database error.', 'danger')
            return render_template('sign_up.html')
        
    return render_template('sign_up.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data
        password = form.password.data
        
        user = db.verify_user(email, password)
        if user:
            session['user_id'] = user['user_id']
            session['email'] = user['email']
            session['role'] = user['user_role']
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
        #sample activities waiting for integation with database from lucas
        (0, "08:00"): "Morning Walk",
        (1, "09:00"): "Yoga Class",        
        (2, "14:00"): "Medical Checkup",
        (3, "11:00"): "Gardening Club", 
        (3, "15:00"): "Book Reading",
        (4, "18:00"): "Cooking Workshop",  
        (5, "10:00"): "Art Therapy",    
        (6, "19:00"): "Movie Night",
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
    query = request.args.get('q', '').strip()
    if query:
        groups = db.search_groups(query)
    else:
        groups = db.get_all_groups()
    return render_template('explore_groups.html', groups=groups, query=query)

@app.route('/groupHome/<int:group_id>')
def group_home(group_id):
    view = request.args.get('view', 'activities')
    search = request.args.get('search', '').strip()

    group = db.get_group_by_id(group_id)
    if not group:
        abort(404)

    if view == "activities":
        activities = db.get_activities_by_group_id(group_id, search)
    else:
        activities = []

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
    # mMUST GET OWNER ID
    proposal_form = InterestGroupProposalForm(request.form)
    if request.method == "POST" and proposal_form.validate():
        db.add_group_proposal(
            proposal_form.name.data,
            proposal_form.topic.data,
            proposal_form.description.data,
            proposal_form.max_size.data,
            proposal_form.join_type.data,
            proposal_form.activity_occurence.data,
            proposal_form.reason.data
        )
        return redirect(url_for("index"))
    return render_template("volunteer/create_interest_group_proposal.html", form=proposal_form)


@app.route("/createActivityProposal", methods=["GET", "POST"])
def create_activity_proposal():
    # CHANGE TO GET ACTIVITY_ID
    proposal_form = ActivityProposalForm(request.form)
    if request.method == "POST" and proposal_form.validate():
        decoded_tags = json.loads(proposal_form.tags.data)
        tags = [tag["value"] for tag in decoded_tags]
        db.add_activity_proposal(
            proposal_form.name.data,
            proposal_form.description.data,
            proposal_form.start_datetime.data,
            proposal_form.end_datetime.data,
            proposal_form.max_size.data,
            proposal_form.funds.data,
            proposal_form.location.data,
            tags,
            proposal_form.remarks.data
        )
        print("succesffully added activity proposal")
        return redirect(url_for("index"))
    return render_template("volunteer/create_group_activity.html", form=proposal_form)


@app.route("/test-discussion")
def discussion_forum():
    return render_template("group_discussion.html")


@app.route('/userProfile/upload', methods=['POST'])
@login_required
def upload_file():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    if 'file' not in request.files:
        return 'No file uploaded', 400

    file = request.files['file']
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)

        filename = f"user_{user_id}_" + filename

        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        db.update_user_profile_pic(user_id, filename)

        return redirect(url_for('user_profile'))

    return 'Invalid file', 400

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('login_google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/callback')
def login_google_callback():
    token = google.authorize_access_token()
    user_info = google.userinfo()
    email = user_info['email']

    # Check if user exists in your DB
    user = db.get_user_by_email(email)
    if not user:
        db.insert_user(
            user_info.get("given_name", ""), 
            user_info.get("family_name", ""), 
            email, 
            '',      # Password empty for SSO
            None     # No default role
        )
        user = db.get_user_by_email(email)
    session['user_id'] = user['user_id']
    session['email'] = email
    session['role'] = user['user_role']
    flash('Logged in with Google!', 'success')

    # If user has no role, force them to choose one
    if not user['user_role']:
        return redirect(url_for('choose_role'))

    return redirect(url_for('explore_groups'))

@app.route('/choose_role', methods=['GET', 'POST'])
def choose_role():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    if request.method == 'POST':
        role = request.form.get('role')
        db.update_user_role(user_id, role)
        session['role'] = role
        flash('Role selected successfully!', 'success')
        return redirect(url_for('explore_groups'))
    return render_template('choose_role.html')

if __name__ == "__main__":
    app.run()