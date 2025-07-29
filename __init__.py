import os
import logging
from flask import Flask, render_template, redirect, url_for, request, abort, session, flash, send_file, has_request_context
from flask_mail import Mail, Message, Attachment
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_executor import Executor
from forms import *
import logging_conf
from logging.config import dictConfig
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

dotenv.load_dotenv()


ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# configuration setup
app = Flask(__name__)
app.config.from_object(config.DevelopmentConfig)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"].encode('utf-8')
app.config["MAIL_PASSWORD"] = os.environ["MAIL_PASSWORD"]
app.config["CSRF_SECRET_KEY"] = os.environ["CSRF_SECRET_KEY"].encode('utf-8')
app.config["SEMATEXT_PASSWORD"] = os.environ["SEMATEXT_PASSWORD"]
app.config["GOOGLE_CLIENT_SECRET"] = os.environ["GOOGLE_CLIENT_SECRET"]
app.config['UPLOAD_FOLDER'] = os.path.join('static', 'uploads')

dictConfig(logging_conf.LOGGING)
app_logger = logging.getLogger('app')

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
executor = Executor(app)

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://",
)

app.register_blueprint(volunteer.volunteer, url_prefix="/volunteer")
app.register_blueprint(admin.admin, url_prefix="/admin")
app.teardown_appcontext(db.close_db)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@executor.job
def send_email(recipient, subject, body):
    msg = Message(f"{subject}", recipients=[f'{recipient}'])
    msg.body = f"{body}"
    mail.send(msg)

def generate_pin(length=6):
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])

@app.route('/')
def index():
    app_logger.info("Home page accessed")
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
            # If MFA is enabled, prompt for code
            if user.get('mfa_enabled'):
                return redirect(url_for('login_mfa'))
            flash('Logged in successfully!', 'success')
            return redirect(url_for('explore_groups'))
    else:
        flash('Invalid credentials.', 'danger')
    return render_template('login.html', form=form)

@app.route('/logout')
def logout():
    app_logger.info("User %s logged out of session", session.get('user_id'))
    session.clear()
    return redirect(url_for('login'))

@app.route('/forgetPassword', methods=['GET', 'POST'])
def forget_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = db.get_user_by_email(email)
        if user:
            pin = generate_pin()
            session['reset_email'] = email
            session['reset_pin'] = pin
            send_email.submit(
                recipient=email,
                subject="Your Social Sage Password Reset PIN",
                body=f"Your password reset PIN is: {pin}\nIf you did not request this, please ignore."
            )
            app_logger.info("PIN sent to user ID %s for password reset", user['user_id'])
            flash('A PIN has been sent to your email. Please enter it below.', 'info')
            return redirect(url_for('enter_pin'))
        else:
            flash('Email not found.', 'danger')
            app_logger.warning("Password reset attempt with non-existent email: %s", email)
    return render_template('forget_password.html')

@app.route('/enterPin', methods=['GET', 'POST'])
def enter_pin():
    if 'reset_email' not in session or 'reset_pin' not in session:
        return redirect(url_for('forget_password'))
    if request.method == 'POST':
        entered_pin = request.form.get('pin')
        if entered_pin == session['reset_pin']:
            flash('PIN verified. Please enter a new password.', 'success')
            return redirect(url_for('change_password'))
        else:
            flash('Incorrect PIN. Please try again.', 'danger')
    return render_template('enter_pin.html')

@app.route('/changePassword', methods=['GET', 'POST'])
def change_password():
    if 'reset_email' not in session or 'reset_pin' not in session:
        return redirect(url_for('forget_password'))
    if request.method == 'POST':
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        if password and confirm_password and password == confirm_password:
            hashed = db.hashed_pw(password)
            db.update_user_password(session['reset_email'], hashed)
            flash('Your password has been changed successfully!', 'success')
            session.pop('reset_email')
            session.pop('reset_pin')
            return redirect(url_for('login'))
        else:
            flash('Passwords do not match or are empty.', 'danger')
    return render_template('change_password.html')

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
    user_id = session.get('user_id')

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
        has_joined=has_joined
    )

@app.route('/join_group/<int:group_id>', methods=['POST'])
def join_group(group_id):
    user_id = session.get('user_id')
    print(f"Joining group: {group_id} as user: {user_id}")
    if not user_id:
        return redirect(url_for('login'))

    db.join_group(user_id, group_id)
    return redirect(url_for('group_home', group_id=group_id))

@app.route('/group/<int:group_id>/activity/<int:activity_id>')
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

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('login_google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/login/callback')
def login_google_callback():
    token = google.authorize_access_token()
    user_info = google.userinfo()
    print("Google user_info:", user_info)  # Debug: see what you get from Google
    email = user_info.get('email')

    if not email:
        flash('Google did not return your email address. Please ensure you have granted permission to share your email.', 'danger')
        return redirect(url_for('login'))

    user = db.get_user_by_email(email)

    if not user:
        db.insert_user(
            user_info.get("given_name", ""), 
            user_info.get("family_name", ""), 
            email, 
            '',      
            None     
        )
    user = db.get_user_by_email(email)

    if not user:
        flash('Error logging in with Google. Please try again.', 'danger')
        return redirect(url_for('login'))

    session['user_id'] = user['user_id']
    session['email'] = email
    session['role'] = user['user_role']
    flash('Logged in with Google!', 'success')

    if not user['user_role']:
        return redirect(url_for('choose_role'))

    return redirect(url_for('explore_groups'))


@app.route('/chooseRole', methods=['GET', 'POST'])
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


@app.context_processor
def inject_profile_pic():
    user_id = session.get('user_id')
    profile_pic = None
    if user_id:
        profile_pic = db.get_user_profile_pic(user_id)
    return {
        'navbar_profile_pic': profile_pic
    }

@app.route('/mfaQrCode')
@login_required
def mfa_qr_code():
    user_id = session['user_id']
    user_email = session['email']
    secret = db.get_user_mfa_secret(user_id)
    if not secret:
        secret = pyotp.random_base32()
        db.update_user_mfa_secret(user_id, secret)
    mfa_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user_email, issuer_name="Social Sage")
    img = qrcode.make(mfa_uri)
    buf = io.BytesIO()
    img.save(buf)
    buf.seek(0)
    return send_file(buf, mimetype='image/png')

@app.route('/setupMfa', methods=['GET', 'POST'])
@login_required
def setup_mfa():
    user_id = session['user_id']
    user_email = session['email']

    # Only generate secret if none exists
    secret = db.get_user_mfa_secret(user_id)
    if not secret:
        secret = pyotp.random_base32()
        db.update_user_mfa_secret(user_id, secret)

    if request.method == 'POST':
        code = request.form.get('code')
        totp = pyotp.TOTP(secret)
        if totp.verify(code):
            db.enable_user_mfa(user_id)
            flash('MFA enabled successfully!', 'success')
            return redirect(url_for('user_profile'))
        else:
            flash('Invalid code, please try again.', 'danger')

    return render_template('verify_mfa.html')  # This template should include <img src="{{ url_for('mfa_qr_code') }}">

@app.route('/loginMfa', methods=['GET', 'POST'])
def login_mfa():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    if request.method == 'POST':
        code = request.form.get('code')
        secret = db.get_user_mfa_secret(user_id)
        totp = pyotp.TOTP(secret)
        if totp.verify(code):
            flash('Logged in with MFA!', 'success')
            return redirect(url_for('explore_groups'))
        else:
            flash('Invalid MFA code.', 'danger')
    return render_template('login_mfa.html')

@app.route('/toggleMfa', methods=['POST'])
@login_required
def toggle_mfa():
    user_id = session['user_id']
    
    # Get current MFA status from DB
    is_mfa_enabled = db.is_user_mfa_enabled(user_id)
    
    if is_mfa_enabled:
        db.disable_user_mfa(user_id)
        flash('MFA disabled.', 'info')
    else:
        secret = db.get_user_mfa_secret(user_id)
        if not secret:
            return redirect(url_for('setup_mfa'))  # First time setup (redirect to QR/code setup)
        db.enable_user_mfa(user_id)
        flash('MFA enabled.', 'success')
    
    return redirect(url_for('user_profile'))

# @app.route("/flagGroup/<int:id>", methods=["POST"])
# def flag_group(id):

#     group = db.get_group_by_id(id)
#     if not group:
#         abort(404, description="Group not found")
#     if group.get("status") != "approved":
#         abort(405, description="Method not allowed for this group")
    
#     flag_form = FlagForm(request.form)
#     if flag_form.validate() and request.method == "POST":
#         reason = flag_form.reason.data
#         db.add_flag_group(id, 1, reason)
#         return redirect(url_for("home"))
    

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
    return render_template('error_page.html', main_message="Unauthorised"), 401

@app.errorhandler(403)
def forbidden_error(error):
    return render_template('error_page.html', main_message="Forbidden"), 403

@app.errorhandler(404)
def not_found_error(error):
    return render_template('error_page.html', main_message="Resource not found"), 404

@app.errorhandler(405)
def method_not_allowed_error(error):
    return render_template('error_page.html', main_message="Method not allowed"), 405

@app.errorhandler(429)
def too_many_requests_error(error):
    return render_template('error_page.html', main_message="Too many requests"), 429

@app.errorhandler(500)
def internal_error(error):
    return render_template('error_page.html', main_message="Internal server error"), 500


if __name__ == "__main__":
    app.run()