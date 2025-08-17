import dotenv
dotenv.load_dotenv()

import os
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
from safe_requests import is_url_safe, safe_fetch
from werkzeug.utils import secure_filename
from access_control import login_required, role_required, group_member_required
import auth
from PIL import Image

dotenv.load_dotenv()

UPLOAD_FOLDER_GROUPS = os.path.join("static", "uploads", "groups")
UPLOAD_FOLDER_ACTIVITIES = os.path.join("static", "uploads", "activities")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app = Flask(__name__)
app.config.from_object(config.DevelopmentConfig)
app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["MAIL_PASSWORD"] = os.environ["MAIL_PASSWORD"]
app.config["CSRF_SECRET_KEY"] = os.environ["CSRF_SECRET_KEY"].encode('utf-8')
app.config["SEMATEXT_PASSWORD"] = os.environ["SEMATEXT_PASSWORD"]
app.config["GOOGLE_CLIENT_SECRET"] = os.environ["GOOGLE_CLIENT_SECRET"]
app.config["UPLOAD_FOLDER_GROUPS"] = UPLOAD_FOLDER_GROUPS
app.config["UPLOAD_FOLDER_ACTIVITIES"] = UPLOAD_FOLDER_ACTIVITIES

os.makedirs(UPLOAD_FOLDER_GROUPS, exist_ok=True)
os.makedirs(UPLOAD_FOLDER_ACTIVITIES, exist_ok=True)

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

def is_valid_image(file_stream):
    try:
        img = Image.open(file_stream)
        img.verify()  # Checks file integrity
        file_stream.seek(0)  # Reset pointer for further use
        return True
    except Exception:
        return False

@app.before_request
def ssrf_guard():
    # Check query params and form data
    for param, value in {**request.args, **request.form}.items():
        if value.startswith("http://") or value.startswith("https://"):
            ok, error = is_url_safe(value)
            if not ok:
                abort(400, f"SSRF Blocked: {error}")

# [FOR ALL] If you are letting user input urls, use safe_fetch as shown below:
#   url = request.args.get("url")
#   resp = safe_fetch(url)
#   return resp.content

@app.route('/')
def index():
    return render_template("home.html")

@app.route('/userProfile', methods=['GET', 'POST'])
@login_required
@limiter.limit("5/minute", methods=["POST"])
def user_profile():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in first.', 'danger')
        return redirect(url_for('auth.login'))

    # Get fresh user data from database
    user = db.get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('auth.login'))

    # Create form and populate with current user data
    if request.method == 'GET':
        form = UserProfileForm()
        form.first_name.data = user['first_name']
        form.last_name.data = user['last_name']
        form.email.data = user['email']

    else:
        form = UserProfileForm(request.form)

    # Get user preferences - using the same pattern as MFA
    mfa_enabled = db.is_user_mfa_enabled(user_id)
    email_notif_enabled = db.is_user_email_notif_enabled(user_id)

    if request.method == 'POST':
        if form.validate():
            success = True
            password_changed = False
            
            # Check if email already exists for another user
            if db.check_email_exists_for_other_user(form.email.data, user_id):
                flash('Email already exists. Please use a different email.', 'danger')
                success = False
            
            # Handle password change if provided
            if form.current_password.data:
                # Verify current password
                if not db.verify_user_password(user_id, form.current_password.data):
                    flash('Current password is incorrect.', 'danger')
                    success = False
                elif form.current_password.data == form.new_password.data:
                    flash('New password must be different from current password.', 'danger')
                    success = False
                elif success:
                    # Update password
                    new_hashed_password = db.hashed_pw(form.new_password.data)
                    if db.update_user_password_by_id(user_id, new_hashed_password):
                        password_changed = True
                    else:
                        flash('Error updating password. Please try again.', 'danger')
                        success = False
            
            # Update basic profile information
            if success:
                
                try:
                    update_result = db.update_user_info(user_id, form.first_name.data, form.last_name.data, form.email.data)
                    
                    if update_result:
                        session['email'] = form.email.data  # Update session if email changes
                        
                        # Show appropriate success message
                        if password_changed:
                            flash('Profile and password updated successfully!', 'success')
                        else:
                            flash('Profile updated successfully!', 'success')
                        
                        
                        # Redirect to prevent form resubmission
                        return redirect(url_for('user_profile'))
                    else:
                        flash('Error updating profile. Please try again.', 'danger')
                except Exception as e:
                    flash('Error updating profile. Please try again.', 'danger')
        else:
            # Display form validation errors
            print(f"DEBUG - Form validation errors: {form.errors}")
            for field, errors in form.errors.items():
                for error in errors:
                    flash(f"{field.replace('_', ' ').title()}: {error}", 'danger')

    return render_template('user_profile.html', user=user, mfa_enabled=mfa_enabled, 
                         email_notif_enabled=email_notif_enabled, form=form)

@app.route('/userProfile/toggleNotifications', methods=['POST'])
@login_required
@limiter.limit("5/minute", methods=["POST"])
def toggle_notifications():
    user_id = session.get('user_id')
    if not user_id:
        flash('Please log in first.', 'danger')
        return redirect(url_for('auth.login'))

    try:
        current_status = db.get_user_notification_status(user_id)
        
        # Toggle the status: if currently 1 (enabled), make it 0 (disabled), and vice versa
        new_status_enabled = (current_status == 0)  # If current is 0, new should be enabled (True)
        new_status_value = 1 if new_status_enabled else 0
        
        # Update the status
        if db.update_user_notification_status(user_id, new_status_enabled):
            if new_status_enabled:
                flash('Email notifications have been enabled.', 'success')
            else:
                flash('Email notifications have been disabled.', 'success')
        else:
            flash('Error updating notification settings. Please try again.', 'danger')
            
    except Exception as e:
        flash('Error updating notification settings. Please try again.', 'danger')
    
    return redirect(url_for('user_profile'))

@app.route('/exploreGroups')
@login_required
@role_required(1, 2)
def explore_groups():
    query = request.args.get('q', '')
    query = query.strip() if query else ''

    if len(query) > 100:
        abort(400, description="Query too long")

    if query:
        groups = db.search_groups(query)
    else:
        groups = db.get_all_groups()

    approved_groups = [g for g in groups if g.get('status_id') == 2]
    app_logger.info("User %s accessed the explore groups page", session["user_id"])
    return render_template('explore_groups.html', groups=approved_groups, query=query)

@app.route('/myGroups')
@role_required(1, 2)
def my_groups():
    user_id = session.get('user_id')
    if not user_id:
        abort(401, description="Access attempt without user session")

    joined_groups = db.get_groups_by_user(user_id)
    if joined_groups is None:
        abort(500, description="Group fetch failed")

    approved_groups = [g for g in joined_groups if g.get('status_id') == 2]
    app_logger.info("User %s accessed his own groups", session["user_id"])
    return render_template('my_groups.html', groups=approved_groups)

@app.route('/groupHome/<int:group_id>')
@role_required(1, 2, 3)
def group_home(group_id):
    view = request.args.get('view', 'activities')
    if view not in ['activities', 'forum']:
        view = 'activities'

    search_query = request.args.get('search', '').strip()

    user_id = session.get('user_id')
    flag_form = FlagForm(request.form)

    group = db.get_group_by_id(group_id)
    if not group:
        app_logger.warning("User %s attempted to find an invalid group of ID %s", session["user_id"], group_id)
        abort(404, description="Unable to find group.")

    join_status_id = db.get_user_group_status_id(user_id, group_id) if user_id else None
    has_joined = join_status_id == 2

    if group['is_public'] == 1 or has_joined:
        activities = db.search_approved_activities_by_group_id(group_id, search_query or None)
    else:
        activities = []

    member_count = db.get_group_member_count(group_id)
    owner = db.get_user_by_id(group["owner"])

    app_logger.info("User %s accessed the group home of group %s", session["user_id"], group["name"])

    return render_template(
        "group_home.html",
        group=group,
        view=view,
        activities=activities,
        has_joined=has_joined,
        join_status_id=join_status_id,
        flag_form=flag_form,
        member_count=member_count,
        owner=owner,
        search_query=search_query
    )


@app.route('/join_group/<int:group_id>', methods=['POST'])
@role_required(1, 2)
@limiter.limit("10/minute;50/day", methods=["POST"])
def join_group(group_id):
    user_id = session.get('user_id')
    if not user_id:
        abort(401, description="Join attempt without login")

    group = db.get_group_by_id(group_id)
    if not group:
        abort(404, description="Join attempt for non-existent group")

    if group.get("status_id") != 2:
        flash("This group is not approved for joining.", "danger")
        app_logger.warning("User %s tried to join unapproved group ID %s", user_id, group_id)
        return redirect(url_for('explore_groups'))

    if group.get("owner") == user_id:
        abort(403, description="You cannot join a group you own")

    member_count = db.get_group_member_count(group_id)
    max_size = group.get("max_size")

    if max_size is not None and member_count >= max_size:
        flash("This group is full and cannot accept more members.", "danger")
        app_logger.info("User %s tried to join full group ID %s", user_id, group_id)
        return redirect(url_for('group_home', group_id=group_id))

    db.join_group(user_id, group_id)

    if not group["is_public"]:
        app_logger.info("User %s has sent a request to join private group %s", session["user_id"], group["name"])
    else:
        app_logger.info("User %s successfully joined group %s", user_id, group_id)
    flash("You have successfully joined the group!", "success")
    return redirect(url_for('group_home', group_id=group_id, group=group))

@app.route('/leave_group/<int:group_id>', methods=['POST'])
@role_required(1, 2)
@limiter.limit("10/minute;50/day", methods=["POST"])
def leave_group(group_id):
    user_id = session.get('user_id')
    if not user_id:
        abort(401, description="Unauthenticated leave attempt.")

    group = db.get_group_by_id(group_id)
    if not group:
        abort(404, description="User attempted to leave a non-existent group.")

    if user_id == group.get("owner"):
        abort(403, description="You cannot leave a group you own.")

    status_id = db.get_user_group_status_id(user_id, group_id)
    if status_id != 2:
        app_logger.warning("User %s attempted to leave group %s without being a full member", user_id, group_id)
        flash("You are not an approved member of this group.", "warning")
        return redirect(url_for('my_groups'))

    db.leave_group(user_id, group_id)
    app_logger.info("User %s left group %s", user_id, group_id)
    flash('You have successfully left the group.', 'info')
    return redirect(url_for('my_groups'))

@app.route('/group/<int:group_id>/activity/<int:activity_id>')
@role_required(1, 2, 3)
@group_member_required(param='group_id')
def view_group_activity(group_id, activity_id):
    group = db.get_group_by_id(group_id)
    if not group:
        abort(404, description="Group not found")

    flag_form = FlagForm(request.form)
    activity = db.get_activity_by_id(activity_id)
    if not activity:
        abort(404, description="Activity not found")

    status_id = db.get_activity_status(activity_id)
    if status_id != 2:
        abort(403, description="You do not have permission to view this activity")


    if activity['group_id'] != group_id:
        abort(403, description="You do not have permission to view this activity")

    registration_count = db.get_activity_registration_count(activity_id)
    is_full = activity["max_size"] is not None and registration_count >= activity["max_size"]
    already_registered = False
    if "user_id" in session:
        already_registered = db.is_user_registered_for_activity(session["user_id"], activity_id)
    app_logger.info("User %s accessed group activity %s from group %s", session["user_id"], activity["name"], group["name"])
    return render_template(
        'activity.html',
        activity=activity,
        group=group,
        registration_count=registration_count,
        is_full=is_full, 
        already_registered=already_registered,
        flag_form=flag_form
    )

@app.route('/register_activity/<int:activity_id>', methods=['POST'])
@role_required(1, 2)
@limiter.limit("10/minute;50/day", methods=["POST"])
def register_activity(activity_id):
    user_id = session.get('user_id')
    if not user_id:
        flash("You must be logged in to register.", "warning")
        return redirect(url_for('login'))

    activity = db.get_activity_by_id(activity_id)
    if not activity:
        flash("Activity not found.", "danger")
        return redirect(url_for('group_home', group_id=activity.get("group_id", 0)))

    group_id = activity.get("group_id")
    if not db.check_user_joined_group(user_id, group_id):
        flash("You must join the group to register for its activities.", "warning")
        return redirect(url_for('group_home', group_id=group_id))
    
    activity_status = db.get_activity_status(activity_id)
    if activity_status != 2:
        flash("This activity is not available for registration.", "danger")
        return redirect(url_for('group_home', group_id=group_id))
    
    group_status = db.get_group_status(activity_id)
    if group_status != 2:
        flash("The group for this activity is not available.", "danger")
        return redirect(url_for('group_home', group_id=group_id))

    if db.is_user_registered_for_activity(user_id, activity_id):
        flash("You are already registered for this activity.", "info")
        return redirect(request.referrer or url_for('home'))

    current_count = db.get_activity_registration_count(activity_id)
    if activity["max_size"] is not None and current_count >= activity["max_size"]:
        flash("This activity has reached its maximum capacity.", "danger")
        return redirect(request.referrer or url_for('home'))

    db.register_user_for_activity(user_id, activity_id)
    flash("Successfully registered for the activity!", "success")
    group = db.get_group_by_id(activity["group_id"])
    app_logger.info("User %s registered for activity %s by group %s", session["user_id"], activity["name"], group["name"])
    return redirect(request.referrer or url_for('home'))

@app.route('/myActivities')
@role_required(1, 2)
def my_activities():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    activities = db.get_registered_activities_by_user(user_id)
    if activities is None:
        abort(500, description="Failed to fetch registered activities")
    return render_template("registered_activities.html", activities=activities)

# @app.route("/test-discussion")
# def discussion_forum():
#     return render_template("group_discussion.html")


@app.route('/userProfile/upload', methods=['POST'])
@login_required
@limiter.limit("5/minute;20/day")
def upload_file():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    if 'file' not in request.files:
        return 'No file uploaded', 400

    file = request.files['file']
    if file and allowed_file(file.filename) and is_valid_image(file.stream):
        filename = secure_filename(file.filename)

        filename = f"user_{user_id}_" + filename

        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        db.update_user_profile_pic(user_id, filename)
        app_logger.info("User %s uploaded a user profile of with filename %s", session["user_id"], filename)
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
@limiter.limit("10/hour;30/day", methods=["POST"])
def flag_group(id):
    group = db.get_group_by_id(id)
    if not group:
        abort(404, description="Group not found")
    if group.get("status_id") != 2:
        abort(405, description="Method not allowed for this group")

    if db.count_flag_group_request(session["user_id"]) >= 3:
        flash("You can only have 3 pending flag requests against interest groups at any time", "danger")
    else:
        flag_form = FlagForm(request.form)
        if flag_form.validate():
            reason = flag_form.reason.data
            db.add_flag_group(group["group_id"], session.get("user_id"), reason)
            flash(f"Successfully submit a flag request for group {group.get('name')}", "success")
            app_logger.info("User %s submitted a flag request to group %s", session.get("user_id"), group.get("group_id"))
        else:
            flash("Error when submitting a flag request, please try again")
    
    return redirect(url_for("group_home", group_id=id))
    

@app.route("/flagActivity/<int:id>", methods=["POST"])
@login_required
@role_required(1, 2)
@limiter.limit("10/hour;30/day", methods=["POST"])
def flag_activity(id):
    activity = db.get_activity_by_id(id)
    if not activity:
        abort(404, description="Activity not found")
    if activity.get("status_id") != 2:
        abort(405, description="Method not allowed for this activity")

    if db.count_flag_activity_request(session["user_id"]) >= 5:
        flash("You can only have 5 pending flag requests against interest activities at any time", "danger")
    else:
        flag_form = FlagForm(request.form)
        if flag_form.validate() and request.method == "POST":
            reason = flag_form.reason.data
            db.add_flag_activity(activity.get("activity_id"), session.get("user_id"), reason)
            flash(f"Successfully sent a flag request for activity {activity.get('name')}", "success")
            app_logger.info("User %s submitted a flag request to activity %s", session.get("user_id"), activity.get("activity_id"))
        else:
            flash("Error when submitting a request, please try again")
    
    return redirect(url_for("view_group_activity", group_id=activity.get("group_id"), activity_id=id))

@app.errorhandler(400)
def bad_request_error(error):
    app_logger.warning("User %s attempted to send a bad request", session.get("user_id"))
    return render_template('error_page.html', main_message="Bad request", description=error.description), 400


@app.errorhandler(401)
def unauthorized_error(error):
    app_logger.warning("User %s attempted to access a protected resource without authentication", session.get("user_id"))
    # add extra stuff to redirect to login
    return render_template('error_page.html', main_message="Unauthorised", description=error.description), 401

@app.errorhandler(403)
def forbidden_error(error):
    app_logger.warning("User %s attempted to access a forbidden resource", session.get("user_id"))
    return render_template('error_page.html', main_message="Forbidden", description=error.description), 403

@app.errorhandler(404)
def not_found_error(error):
    app_logger.warning("User %s attempted to find an invalid URL", session.get("user_id"))
    return render_template('error_page.html', main_message="Resource not found", description=error.description), 404

@app.errorhandler(405)
def method_not_allowed_error(error):
    app_logger.warning("User %s attempted an invalid %s method", session.get("user_id"), request.method)
    return render_template('error_page.html', main_message="Method not allowed", description=error.description), 405


@app.errorhandler(413)
def entity_too_large(error):
    app_logger.warning("User %s attempted to uplooad data that exceeds the maximum limit.", session.get("user_id"))
    return render_template('error_page.html', main_message="Request entity too large", description=error.description), 405

@app.errorhandler(429)
def too_many_requests_error(error):
    app_logger.warning("Too many requests from IP: %s", request.remote_addr)
    return (render_template('error_page.html', main_message="Too many requests", description=error.description), 429)

@app.errorhandler(500)
def internal_error(error):
    app_logger.exception("An internal error occurred:\n %s", error)
    return render_template('error_page.html', main_message="Internal server error", description=None), 500


# if __name__ == "__main__":
#     app.run()


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        ssl_context=('certs/127.0.0.1+1.pem', 'certs/127.0.0.1+1-key.pem'),
        debug=True
    )
