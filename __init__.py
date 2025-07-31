import dotenv
dotenv.load_dotenv()
import json
import os
from flask import Flask, render_template, redirect, url_for, request, abort, session, flash, send_file
import logging
from logging.config import dictConfig
import logging_conf
from flask import Flask, render_template, redirect, url_for, request, abort, session, flash, send_file, has_request_context
from utils import mail, executor, limiter, send_email, oauth
from forms import *
import db
import config
import admin
import volunteer
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta
from access_control import login_required, role_required, group_member_required
from authlib.integrations.flask_client import OAuth
import random
import pyotp
import qrcode
import io
import auth

dotenv.load_dotenv()


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config.from_object(config.DevelopmentConfig)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["MAIL_PASSWORD"] = os.environ["MAIL_PASSWORD"]
app.config["CSRF_SECRET_KEY"] = os.environ["CSRF_SECRET_KEY"].encode('utf-8')
app.config["SEMATEXT_PASSWORD"] = os.environ["SEMATEXT_PASSWORD"]
app.config["GOOGLE_CLIENT_SECRET"] = os.environ["GOOGLE_CLIENT_SECRET"]
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

mail.init_app(app)
executor.init_app(app)
limiter.init_app(app)
oauth.init_app(app)

dictConfig(logging_conf.LOGGING)
app_logger = logging.getLogger('app')

app.register_blueprint(volunteer.volunteer, url_prefix="/volunteer")
app.register_blueprint(admin.admin, url_prefix="/admin")
app.register_blueprint(auth.auth, url_prefix="/auth")
app.teardown_appcontext(db.close_db)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template("home.html")


@app.route('/userProfile', methods=['GET', 'POST'])
def user_profile():
    user_id = session.get('user_id')
    mfa_enabled = db.is_user_mfa_enabled(user_id)
    if not user_id:
        return redirect(url_for('login'))

    user = db.get_user_by_id(user_id)

    if request.method == 'POST':
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        email = request.form.get('email')
        if first_name and last_name and email:
            db.update_user_info(user_id, first_name, last_name, email)
            session['email'] = email  # Update session if email changes
            flash('Profile updated successfully!', 'success')
            # Refresh user info after update
            user = db.get_user_by_id(user_id)
        else:
            flash('All fields are required.', 'danger')

    return render_template('user_profile.html', user=user, mfa_enabled=mfa_enabled)


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
@role_required(1, 2)
def explore_groups():
    query = request.args.get('q', '').strip()
    if query:
        groups = db.search_groups(query)
    else:
        groups = db.get_all_groups()
    return render_template('explore_groups.html', groups=groups, query=query)

@app.route('/myGroups')
@role_required(1, 2)
def my_groups():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    joined_groups = db.get_groups_by_user(user_id)
    return render_template('my_groups.html', groups=joined_groups)

@app.route('/groupHome/<int:group_id>')
@role_required(1, 2, 3)
def group_home(group_id):
    view = request.args.get('view', 'activities')
    user_id = session.get('user_id')
    flag_form = FlagForm(request.form)

    group = db.get_group_by_id(group_id)
    if not group:
        abort(404)

    has_joined = db.check_user_joined_group(user_id, group_id) if user_id else False

    if group['is_public'] == 1 or has_joined:
        activities = db.get_activities_by_group_id(group_id)
    else:
        activities = []

    return render_template(
        "group_home.html",
        group=group,
        view=view,
        activities=activities,
        has_joined=has_joined,
        flag_form=flag_form
    )

@app.route('/join_group/<int:group_id>', methods=['POST'])
@role_required(1, 2)
def join_group(group_id):
    user_id = session.get('user_id')
    print(f"Joining group: {group_id} as user: {user_id}")
    if not user_id:
        return redirect(url_for('login'))

    db.join_group(user_id, group_id)
    return redirect(url_for('group_home', group_id=group_id))

@app.route('/group/<int:group_id>/activity/<int:activity_id>')
@role_required(1, 2, 3)
@group_member_required(param='group_id')
def view_group_activity(group_id, activity_id):
    group = db.get_group_by_id(group_id)
    if not group:
        abort(404)

    activity = db.get_activity_by_id(activity_id)
    if not activity or activity['group_id'] != group_id:
        abort(404)

    return render_template('activity.html', activity=activity, group=group)



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

@app.context_processor
def inject_profile_pic():
    user_id = session.get('user_id')
    profile_pic = None
    if user_id:
        profile_pic = db.get_user_profile_pic(user_id)
    return {
        'navbar_profile_pic': profile_pic
    }


@app.route("/flagGroup/<int:id>", methods=["POST"])
@login_required
@role_required(1, 2)
def flag_group(id):
    group = db.get_group_by_id(id)
    if not group:
        abort(404, description="Group not found")
    if group.get("status_id") != 2:
        abort(405, description="Method not allowed for this group")
    
    flag_form = FlagForm(request.form)
    if flag_form.validate():
        reason = flag_form.reason.data
        db.add_flag_group(group["group_id"], session.get("user_id"), reason)
    return redirect(url_for("explore_groups"))
    

# @app.route("/flagActivity/<int:id>", methods=["POST"])
# def flag_activity(id):
#     activity = db.get_activity_by_id(id)
#     if not activity:
#         abort(404, description="Activity not found")
#     if activity.get("status") != "approved":
#         abort(405, description="Method not allowed for this activity")
    
#     flag_form = FlagActivityForm(request.form)
#     if flag_form.validate() and request.method == "POST":
#         reason = flag_form.reason.data
#         db.add_flag_activity(id, 1, reason


@app.errorhandler(401)
def unauthorized_error(error):
    app_logger.warning("User %s attempted to access a protected resource without authentication", session.get("user_id"))
    # add extra stuff to redirect to login
    return render_template('error_page.html', main_message="Unauthorised"), 401

@app.errorhandler(403)
def forbidden_error(error):
    app_logger.warning("User %s attempted to access a forbidden resource", session.get("user_id"))
    return render_template('error_page.html', main_message="Forbidden"), 403

@app.errorhandler(404)
def not_found_error(error):
    app_logger.warning("User %s attempted to find an invalid URL", session.get("user_id"))
    return render_template('error_page.html', main_message="Resource not found"), 404

@app.errorhandler(405)
def method_not_allowed_error(error):
    app_logger.warning("User %s attempted an invalid %s method", session.get("user_id"), request.method)
    return render_template('error_page.html', main_message="Method not allowed"), 405

@app.errorhandler(429)
def too_many_requests_error(error):
    app_logger.warning("Too many requests from IP: %s", request.remote_addr)
    return render_template('error_page.html', main_message="Too many requests"), 429

@app.errorhandler(500)
def internal_error(error):
    app_logger.exception("An internal error occurred:\n %s", error)
    return render_template('error_page.html', main_message="Internal server error"), 500


if __name__ == "__main__":
    app.run()