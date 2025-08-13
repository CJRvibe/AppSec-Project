from flask import Flask, render_template, redirect, url_for, request, abort, session, Blueprint, flash
from utils import mail, limiter, send_email
import logging
import db
from forms import CreateAdminForm

admin = Blueprint("admin", __name__, template_folder="templates")
app_logger = logging.getLogger("app")

update_limit = limiter.shared_limit("20/hour;50/day", methods=["POST"], scope="group and activity proposal update")

@admin.before_request # access control for admin
def check_is_admin():
    if "user_id" not in session:
        abort(401, description="You are not authenticated, please login")
    elif session.get("role") != 3:
        abort(403, description="You are not authorised to access this page")

@admin.route("/")
def home():
    user_id = session.get("user_id")

    try:
        app_logger.info("Admin %s accessed admin home", user_id)

        user_count = db.get_total_users()
        group_count = db.get_total_groups()
        activity_count = db.get_total_activities()
        growth_data = db.get_user_growth_last_7_days()

        if growth_data is None:
            app_logger.warning("No user growth data found for admin %s", user_id)
            growth_data = []

        dates = [row["day"].strftime("%Y-%m-%d") for row in growth_data]
        counts = [row["count"] for row in growth_data]

        return render_template(
            "admin/admin_home.html",
            user_count=user_count,
            group_count=group_count,
            activity_count=activity_count,
            growth_dates=dates,
            growth_counts=counts
        )

    except Exception as e:
        app_logger.exception("Error in admin home for user %s: %s", user_id, str(e))
        abort(500)

@admin.route("/interestGroups/proposals")
def manage_group_proposals():
    groups = db.admin_get_groups(type="pending")
    app_logger.info("Admin %s accessed group proposals", session.get("user_id"))
    return render_template("admin/manage_groups.html", groups=groups, type="pending")


@admin.route("/interestGroups")
def manage_active_groups():
    groups = db.admin_get_groups()
    app_logger.info("Admin %s accessed active groups", session.get("user_id"))
    return render_template("admin/manage_groups.html", groups=groups, type="approved")


@admin.route("/interestGroups/rejectedGroups")
def manage_reject_groups():
    groups = db.admin_get_groups(type="rejected")
    app_logger.info("Admin %s accessed rejected groups", session.get("user_id"))
    return render_template("admin/manage_groups.html", groups=groups, type="rejected")


@admin.route("/interestGroups/suspendedGroups")
def manage_suspended_groups():
    groups = db.admin_get_groups(type="suspended")
    app_logger.info("Admin %s accessed suspended groups", session.get("user_id"))
    return render_template("admin/manage_groups.html", groups=groups, type="suspended")


@admin.route("/interestGroups/<int:id>")
def view_group(id):
    group = db.admin_get_group_by_id(id)
    if group:
        app_logger.info("Admin %s accessed group %s information", session.get("user_id"), group.get("group_id"))
        return render_template("admin/view_group.html", group=group)
    else:
        abort(404, description="Group not found")


@admin.route("/interestGroups/approveGroupProposal/<int:id>", methods=["POST"])
@update_limit
def approve_group_proposal(id):
    group = db.admin_get_group_by_id(id)

    if not group:
        abort(404, description="Group not found")
    elif group and group.get("status") != "pending":
        abort(405, description="Method not allowed for this group")
    else:
        db.admin_update_group_proposal(id, approved=True)
        app_logger.info("Admin %s approved proposal of group %s", session.get("user_id"), group.get("group_id"))
        db.admin_join_group(group["owner"], group["group_id"])
        
        user = db.get_user_by_id(group["owner"])
        if user["email_notif"]:
            send_email.submit(user["email"], f"Group {group['group_id']} Approved", f"Your pending proposal for group {group['name']} has successfully been approved")
            app_logger.info(f"Email successfully send to User {group['owner']} to notify of group approval")

        return redirect(url_for(".manage_active_groups"))


@admin.route("/interestGroups/rejectGroupProposal/<int:id>", methods=["POST"])
@update_limit
def reject_group_proposal(id):
    group = db.admin_get_group_by_id(id)

    if not group:
        abort(404, description="Group not found")
    elif group and group.get("status") != "pending":
        abort(405, description="Method not allowed for this group")
    else:
        db.admin_update_group_proposal(id, approved=False)
        app_logger.info("Admin %s rejected proposal of group %s", session.get("user_id"), group.get("group_id"))

        user = db.get_user_by_id(group["owner"])

        if user["email_notif"]:
            send_email.submit(user["email"], f"Group {group['group_id']} Rejected", f"Your pending proposal for group {group['name']} has been rejected. Please try again and ensure all information is as accurate as possible.")
            app_logger.info(f"Email successfully send to User {group['owner']} to notify of group rejection")

        return redirect(url_for(".manage_reject_groups"))


@admin.route("/groupActivities")
def manage_approved_activities():
    activities = db.admin_get_group_activities(type="approved")
    app_logger.info("Admin %s accessed approved group activities", session.get('user_id'))
    return render_template("admin/manage_activities.html", activities=activities, type="approved")


@admin.route("/groupActivities/activityProposals")
def manage_pending_activities():
    activities = db.admin_get_group_activities(type="pending")
    app_logger.info("Admin %s accessed activity proposals", session.get("user_id"))
    return render_template("admin/manage_activities.html", activities=activities, type="pending")


@admin.route("/gropupActivities/rejectedActivities")
def manage_rejected_activities():
    activities = db.admin_get_group_activities(type="rejected")
    app_logger.info("Admin %s accessed rejected activities", session.get("user_id"))
    return render_template("admin/manage_activities.html", activities=activities, type="rejected")


@admin.route("/groupActivities/<int:id>")
def view_activity(id):
    activity = db.admin_get_group_activity(id)

    if activity:
        app_logger.info("Admin %s accessed activity %s information", session.get("user_id"), activity.get("activity_id"))
        return render_template("admin/view_activity.html", activity=activity)
    else: abort(404, description="Activity not found")


@admin.route("/groupActivities/approveActivity/<int:id>", methods=["POST"])
@update_limit
def approve_activity(id):
    activity = db.admin_get_group_activity(id)

    if not activity:
        abort(404, description="Activity not found")
    elif activity and activity.get("status") != "pending":
        abort(405, description="Method not allowed for this activity")
    else:
        db.admin_update_activity_proposal(id, approved=True)
        app_logger.info("Admin %s approved activity %s", session.get("user_id"), activity.get("activity_id"))

        group = db.admin_get_group_by_id(activity["group_id"])
        user = db.get_user_by_id(group["owner"])

        if user["email_notif"]:
            send_email.submit(user["email"], f"Activity {activity['activity_id']} Approved", f"Your pending proposal for group {activity['name']} has successfully been approved")
            app_logger.info(f"Email successfully send to User {group['owner']} to notify of activity approval")
            
        return redirect(url_for(".manage_approved_activities"))


@admin.route("/groupActivities/rejectActivity/<int:id>", methods=["POST"])
@update_limit
def reject_activity(id):
    activity = db.admin_get_group_activity(id)

    if not activity:
        abort(404, description="Activity not found")
    elif activity and activity.get("status") != "pending":
        abort(405, description="Method not allowed for this activity")
    else:
        db.admin_update_activity_proposal(id, approved=False)
        app_logger.info("Admin %s rejected %s", session.get("user_id"), activity.get("activity_id"))

        group = db.admin_get_group_by_id(activity["group_id"])
        user = db.get_user_by_id(group["owner"])

        if user["email_notif"]:
            send_email.submit(user["email"], f"Activity {activity['activity_id']} Rejected", f"Your pending proposal for group {activity['name']} has been rejected. Please try again and ensure all information is as accurate as possible.")
            app_logger.info(f"Email successfully send to User {group['owner']} to notify of activity rejection")
        
        return redirect(url_for(".manage_rejected_activities"))

@admin.route('/users', methods=['GET'])
def admin_view_users():
    roles = [
        {"label": "All", "value": ""},
        {"label": "Elderly", "value": 1},
        {"label": "Volunteer", "value": 2},
        {"label": "Admin", "value": 3}
    ]

    selected_role = request.args.get('role', '')
    current_user_id = session.get('user_id')

    if selected_role != '':
        users = db.get_users_by_role(int(selected_role))
        app_logger.info("Admin %s accessed information of all %s role users", current_user_id, selected_role)
    else:
        users = db.get_all_users()
        app_logger.info("Admin %s accessed information of all users", current_user_id)

    # Add current user email to session for template access
    current_user = db.get_user_by_id(current_user_id)
    if current_user:
        session['email'] = current_user['email']

    return render_template(
        "admin/manage_users.html",
        users=users,
        roles=roles,
        selected_role=selected_role
    )


@admin.route("/interestGroups/flaggedRequests")
def manage_flagged_groups():
    flagged_groups = db.admin_get_flagged_groups()
    app_logger.info("Admin %s accessed information for all flag group requests", session.get("user_id"))
    return render_template("admin/manage_flagged_groups.html", flagged_groups=flagged_groups)


@admin.route("/interestActivities/flaggedRequests")
def manage_flagged_activities():
    flagged_activities = db.admin_get_flagged_activities()
    app_logger.info("Admin %s accessed information for all flag activity requests", session.get("user_id"))
    return render_template("admin/manage_flagged_activities.html", flagged_activities=flagged_activities)


@admin.route("/interestGroups/flaggedRequests/approve/<int:flag_id>", methods=["POST"])
@update_limit
def approve_group_flag(flag_id: int):
    flag_group = db.admin_get_flagged_group(flag_id)
    if not flag_group:
        abort(404, description="Flagged request not found")
    elif flag_group and flag_group["status_id"] != 1:
        abort(405, description="Method not allowed for this flag request")
    else:
        db.admin_update_group_flag_request(flag_id, approved=True)
        app_logger.info("Admin %s approved group flag request %s from user %s", session.get("user_id"), flag_group.get("flag_id"), flag_group.get("user_id"))

        user = db.get_user_by_id(flag_group["user_id"])
        if user["email_notif"]:
            group = db.admin_get_group_by_id(flag_group["group_id"])
            send_email.submit(user["email"], f"Group Flag Request {flag_group['flag_id']} Approved", f"Your pending flag request against the group {group['name']} has successfully been approved")
            app_logger.info(f"Email successfully send to User {group['owner']} to notify of flag group approval")

        return redirect(url_for(".manage_flagged_groups"))


@admin.route("/interestGroups/flaggedRequests/reject/<int:flag_id>", methods=["POST"])
@update_limit
def reject_group_flag(flag_id: int):
    flag_group = db.admin_get_flagged_group(flag_id)
    print(flag_group)
    if not flag_group:
        abort(404, description="Flagged request not found")
    elif flag_group and flag_group["status_id"] != 1:
        abort(405, description="Method not allowed for this flag request")
    else:
        db.admin_update_group_flag_request(flag_id, approved=False)
        app_logger.info("Admin %s rejected group flag request %s from user %s", session.get("user_id"), flag_group.get("flag_id"), flag_group.get("user_id"))

        user = db.get_user_by_id(flag_group["user_id"])
        if user["email_notif"]:
            group = db.admin_get_group_by_id(flag_group["group_id"])
            send_email.submit(user["email"], f"Group Flag Request {flag_group['flag_id']} Rejected", f"Your pending flag request against the group {group['name']} has been rejected.")
            app_logger.info(f"Email successfully send to User {group['owner']} to notify of flag group rejection")

        return redirect(url_for(".manage_flagged_groups"))
    

@admin.route("/interestActivities/flaggedRequests/approve/<int:flag_id>", methods=["POST"])
@update_limit
def approve_activity_flag(flag_id:int):
    flag_activity = db.admin_get_flagged_activity(flag_id)
    if not flag_activity:
        abort(404, description="Flagged request not found")
    elif flag_activity and flag_activity["status_id"] != 1:
        abort(405, description="Method not allowed for this flag request")
    else:
        db.admin_update_activity_flag_request(flag_id, approved=True)
        app_logger.info("Admin %s approved activity flag request %s from user %s", session.get("user_id"), flag_activity.get("flag_id"), flag_activity.get("user_id"))

        user = db.get_user_by_id(flag_activity["user_id"])
        if user["email_notif"]:
            group = db.admin_get_group_by_id(flag_activity["activity_id"])
            send_email.submit(user["email"], f"Activity Flag Request {flag_activity['flag_id']} Approved", f"Your pending flag request against the activity {group['name']} has successfully been approved")
            app_logger.info(f"Email successfully send to User {group['owner']} to notify of flag group approval")

        return redirect(url_for(".manage_flagged_activities"))
    

@admin.route("/interestActivities/flaggedRequests/reject/<int:flag_id>", methods=["POST"])
@update_limit
def reject_activity_flag(flag_id:int):
    flag_activity = db.admin_get_flagged_activity(flag_id)
    if not flag_activity:
        abort(404, description="Flagged request not found")
    elif flag_activity and flag_activity["status_id"] != 1:
        abort(405, description="Method not allowed for this flag request")
    else:
        db.admin_update_activity_flag_request(flag_id, approved=False)
        app_logger.info("Admin %s rejected activity flag request %s from user %s", session.get("user_id"), flag_activity.get("flag_id"), flag_activity.get("user_id"))

        user = db.get_user_by_id(flag_activity["user_id"])
        if user["email_notif"]:
            group = db.admin_get_group_by_id(flag_activity["activity_id"])
            send_email.submit(user["email"], f"Activity Flag Request {flag_activity['flag_id']} Rejected", f"Your pending flag request against the activity {group['name']} has been rejected.")
            app_logger.info(f"Email successfully send to User {group['owner']} to notify of flag group rejection")

        return redirect(url_for(".manage_flagged_activities"))
    

@admin.route("interestGroups/suspend/<int:id>", methods=["POST"])
def suspend_group(id):
    group = db.admin_get_group_by_id(id)

    if not group:
        abort(404, description="Group not found")
    elif group and group.get("status") != "approved":
        abort(405, description="Method not allowed for this group")
    else:
        db.admin_suspend_group(id)
        app_logger.info("Admin %s suspended group %s", session.get("user_id"), group.get("group_id"))
        
        user = db.get_user_by_id(group["owner"])
        if user["email_notif"]:
            send_email.submit(user["email"], f"Group {group['group_id']} Suspended", f"Your active group {group['name']} has been approved suspended. This was a decision made by the admins. If you have any queries, please contact us.")
            app_logger.info(f"Email successfully send to User {group['owner']} to notify of group suspension")

        return redirect(url_for(".manage_suspended_groups"))


@admin.route('/users/<int:user_id>/suspend', methods=['POST'])
@limiter.limit("10/minute;20/hour;50/day")
def suspend_user(user_id):
    current_user_id = session.get('user_id')
    
    # Prevent self-suspension
    if user_id == current_user_id:
        flash('You cannot suspend your own account.', 'danger')
        app_logger.warning("Admin %s attempted to suspend their own account", current_user_id)
        return redirect(url_for('admin.admin_view_users'))
    
    # Check if current user can suspend the target user
    if not db.can_suspend_user(current_user_id, user_id):
        user = db.get_user_by_id(user_id)
        if user and user.get('user_role') == 3:
            flash('You do not have permission to suspend other administrators.', 'danger')
        else:
            flash('You do not have permission to perform this action.', 'danger')
        app_logger.warning("Admin %s attempted to suspend user %s without permission", current_user_id, user_id)
        return redirect(url_for('admin.admin_view_users'))
    
    user = db.get_user_by_id(user_id)
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('admin.admin_view_users'))
    
    # Root admin cannot be suspended
    if db.is_root_admin_by_email(user['email']):
        flash('The root administrator cannot be suspended.', 'danger')
        app_logger.warning("Admin %s attempted to suspend root admin", current_user_id)
        return redirect(url_for('admin.admin_view_users'))
    
    current_status = db.get_user_suspension_status(user_id)
    new_status = 0 if current_status == 1 else 1  
    
    if db.update_user_suspension_status(user_id, new_status):
        action = "suspended" if new_status == 1 else "activated"
        flash(f'User {user["first_name"]} {user["last_name"]} has been {action}.', 'success')
        app_logger.info("Admin %s %s user %s (%s)", current_user_id, action, user_id, user['email'])
        
        # Send email notification if user has email notifications enabled
        if user.get('email_notif') and new_status == 1:  # Only notify on suspension
            try:
                send_email.submit(
                    recipient=user['email'],
                    subject="Social Sage - Account Suspended",
                    body=f"Your account has been suspended. Please contact support at socialsage.@gmail.com for assistance."
                )
            except Exception as e:
                app_logger.error("Failed to send suspension email to %s: %s", user['email'], str(e))
    else:
        app_logger.error("Failed to update suspension status for user %s", user_id)

    return redirect(url_for('admin.admin_view_users'))

def root_admin_required(f):
    """Decorator to ensure only root admin can access certain routes"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = session.get('user_id')
        if not db.is_root_admin(current_user_id):
            flash('Access denied. Root administrator privileges required.', 'danger')
            app_logger.warning("Non-root admin %s attempted to access root-only function: %s", 
                             current_user_id, f.__name__)
            return redirect(url_for('.admin_view_users'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/users/create', methods=['GET', 'POST'])
@root_admin_required
def create_admin_user():
    current_user_id = session.get('user_id')
    
    if not db.is_root_admin(current_user_id):
        flash('Only the root administrator can create admin users.', 'danger')
        app_logger.warning("Non-root admin %s attempted to access admin creation page", current_user_id)
        return redirect(url_for('.admin_view_users'))
    
    form = CreateAdminForm(request.form)
    
    if request.method == 'POST':
        if form.validate():
            hashed_password = db.hashed_pw(form.password.data)
            
            success = db.insert_user(
                form.first_name.data,
                form.last_name.data,
                form.email.data,
                hashed_password,
                3  
            )
            
            if success:
                flash('Admin user created successfully!', 'success')
                app_logger.info("Root admin %s created new admin user with email %s", 
                               current_user_id, form.email.data)
                return redirect(url_for('.admin_view_users'))
            else:
                flash('Error creating admin user. Please try again.', 'danger')
                app_logger.error("Failed to create admin user with email %s", form.email.data)
        else:
            app_logger.warning("Root admin %s submitted invalid admin creation form", current_user_id)
    
    return render_template('admin/create_admin_user.html', form=form)