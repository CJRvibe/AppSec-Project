from flask import Blueprint, render_template, redirect, url_for, session, request, abort, flash
from flask import current_app as app
from forms import *
from utils import limiter
from werkzeug.utils import secure_filename
import json
import logging
import db
import uuid
import os

from access_control import role_required

volunteer = Blueprint("volunteer", __name__, template_folder="templates")
app_logger = logging.getLogger("app")

@volunteer.route('/dashboard/<int:group_id>')
@role_required(2)
def dashboard(group_id):
    user_id = session.get("user_id")
    if not user_id:
        abort(401, description="Unauthorized access to dashboard")

    group = db.get_group_by_id(group_id)
    if not group:
        abort(404, description="Group not found")

    if group.get("owner") != user_id:
        abort(403, description="You do not have permission to access this group")

    activities = db.get_activities_by_group_id(group_id)
    pending_users = db.get_pending_users_by_group(group_id)
    joined_users = db.get_approved_users_by_group(group_id)

    return render_template(
        "volunteer/dashboard.html",
        group=group,
        group_id=group["group_id"],
        activities=activities,
        pending_users=pending_users,
        joined_users=joined_users
    )

@volunteer.route("/dashboard/<int:group_id>/approve_user/<int:user_id>", methods=["POST"])
@role_required(2)
@limiter.limit("20/hour;60/day")
def approve_user(group_id, user_id):
    current_user_id = session.get("user_id")
    if not current_user_id:
        abort(401, description="Unauthorized access to approve user")

    group = db.get_group_by_id(group_id)
    if not group:
        abort(404, description="Group not found")

    if group.get("owner") != current_user_id:
        abort(403, description="You do not have permission to approve users in this group")

    db.approve_user(user_id, group_id)
    flash("User approved.", "success")
    return redirect(url_for("volunteer.dashboard", group_id=group_id, view="users"))

@volunteer.route("/dashboard/<int:group_id>/remove_user/<int:user_id>", methods=["POST"])
@role_required(2)
@limiter.limit("1/second;20/hour;60/day")
def remove_user(group_id, user_id):
    current_user_id = session.get("user_id")
    if not current_user_id:
        abort(401, description="Unauthorized access to remove user")

    group = db.get_group_by_id(group_id)
    if not group:
        abort(404, description="Group not found")

    if group.get("owner") != current_user_id:
        abort(403, description="You do not have permission to remove users from this group")

    db.remove_user_from_group(user_id, group_id)
    flash("User removed from group.", "warning")
    return redirect(url_for("volunteer.dashboard", group_id=group_id, view="users"))

@volunteer.route("/dashboard/<int:group_id>/remove_activity/<int:activity_id>", methods=["POST"])
@role_required(2)
def remove_activity(group_id, activity_id):
    user_id = session.get("user_id")
    if not user_id:
        abort(401, description="Unauthorized access to remove activity")

    group = db.get_group_by_id(group_id)
    if not group:
        abort(404, description="Group not found")

    if group.get("owner") != user_id:
        abort(403, description="You do not have permission to remove activities from this group")

    activity = db.get_activity_by_id(activity_id)
    if not activity or activity.get("group_id") != group_id:
        abort(404, description="Activity not found or does not belong to this group")

    db.remove_activity(activity_id)
    flash("Activity removed.", "warning")
    return redirect(url_for("volunteer.dashboard", group_id=group_id, view="activities"))

@volunteer.route("/createInterestGroupProposal", methods=["GET", "POST"])
@role_required(2)
@limiter.limit("3/hour;7/day", methods=["POST"])
def create_group_proposal():
    user_id = session.get("user_id")
    if not user_id:
        abort(401, description="Unauthorized access to create group proposal")

    proposal_form = InterestGroupProposalForm(request.form)

    if request.method == "POST":
        if proposal_form.validate():
            file = request.files.get("picture")
            filename = None

            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER_GROUPS"], filename))

            db.add_group_proposal(
                proposal_form.name.data,
                proposal_form.topic.data,
                proposal_form.description.data,
                proposal_form.max_size.data,
                proposal_form.join_type.data,
                proposal_form.activity_occurence.data,
                proposal_form.reason.data,
                user_id,
                filename
            )
            app_logger.info("User %s successfully submitted a group proposal: %s", user_id, proposal_form.name.data)
            flash("Group proposal submitted successfully!", "success")
            return redirect(url_for("explore_groups"))
        else:
            app_logger.warning("Validation failed for group proposal submitted by user %s: %s", user_id, proposal_form.errors)
            flash("There were errors in your submission. Please review and try again.", "danger")

    return render_template("volunteer/create_interest_group_proposal.html", form=proposal_form)

@volunteer.route("/createActivityProposal/<int:group_id>", methods=["GET", "POST"])
@role_required(2)
@limiter.limit("5/hour;10/day", methods=["POST"])
def create_activity_proposal(group_id):
    user_id = session.get("user_id")
    if not user_id:
        abort(401, description="Unauthorized access to create activity proposal")

    group = db.get_group_by_id(group_id)
    if not group:
        abort(404, description="Group not found")

    if group["owner"] != user_id:
        abort(403, description="You do not have permission to propose activities for this group")

    if group["status_id"] != 2:
        flash("You can only create activities for approved groups.", "danger")
        return redirect(url_for("volunteer.dashboard", group_id=group_id))

    proposal_form = ActivityProposalForm(request.form)

    if request.method == "POST":
        if proposal_form.validate():
            decoded_tags = json.loads(proposal_form.tags.data or "[]")
            tags = [tag.get("value") for tag in decoded_tags if "value" in tag]
            file = request.files.get("picture")
            filename = None
            if file and file.filename:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config["UPLOAD_FOLDER_ACTIVITIES"], filename))
            db.add_activity_proposal(
                proposal_form.name.data,
                proposal_form.description.data,
                proposal_form.start_datetime.data,
                proposal_form.end_datetime.data,
                proposal_form.max_size.data,
                proposal_form.funds.data,
                proposal_form.location.data,
                tags,
                proposal_form.remarks.data,
                group_id,
                filename
            )
            app_logger.info("Activity proposal submitted by user %s for group %s", user_id, group_id)
            flash("Activity proposal submitted successfully.", "success")
            return redirect(url_for("volunteer.dashboard", group_id=group_id))
        else:
            app_logger.warning("Validation errors for activity proposal: %s", proposal_form.errors)
            flash("Please correct the errors in the form.", "danger")

    return render_template("volunteer/create_group_activity.html", form=proposal_form, group=group)

@volunteer.route('/dashboard')
@role_required(2)
def volunteer_dashboard_groups():
    user_id = session.get('user_id')
    if not user_id:
        abort(401, description="Unauthorized access to volunteer dashboard")

    groups = db.get_groups_by_owner(user_id)
    if groups is None:
        abort(404, description="No groups found for this user")
        groups = []

    return render_template('volunteer/group_list_dashboard.html', groups=groups)

@volunteer.route("/dashboard/<int:group_id>/reject_user/<int:user_id>", methods=["POST"])
@role_required(2)
def reject_user(group_id, user_id):
    user = session.get("user_id")
    group = db.get_group_by_id(group_id)

    if not group or group["owner"] != user:
        abort(403, description="You do not have permission to reject users in this group")

    db.reject_user(user_id, group_id)
    flash("User join request has been rejected.", "warning")

    return redirect(url_for("volunteer.dashboard", group_id=group_id, view="users"))
