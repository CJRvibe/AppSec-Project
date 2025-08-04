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
        app_logger.warning("Unauthenticated user attempted to access volunteer dashboard.")
        return redirect(url_for("login"))

    group = db.get_group_by_id(group_id)
    if not group:
        app_logger.warning("Group ID %s not found during dashboard access by user %s", group_id, user_id)
        abort(404)

    if group.get("owner") != user_id:
        app_logger.warning("User %s attempted unauthorized access to dashboard for group %s", user_id, group_id)
        abort(403)

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

        #app_logger.exception("Error accessing volunteer dashboard (user: %s, group: %s): %s", session.get("user_id"), group_id, str(e))
       # abort(500)

@volunteer.route("/dashboard/<int:group_id>/approve_user/<int:user_id>", methods=["POST"])
@role_required(2)
@limiter.limit("20/hour;60/day")
def approve_user(group_id, user_id):
    try:
        current_user_id = session.get("user_id")
        if not current_user_id:
            app_logger.warning("Unauthenticated access attempt to approve user in group %s", group_id)
            return redirect(url_for("login"))

        group = db.get_group_by_id(group_id)
        if not group:
            app_logger.warning("Group ID %s not found during approve_user by user %s", group_id, current_user_id)
            abort(404)

        if group.get("owner") != current_user_id:
            app_logger.warning("User %s tried to approve user %s in unauthorized group %s", current_user_id, user_id, group_id)
            abort(403)

        db.approve_user(user_id, group_id)
        flash("User approved.", "success")
        return redirect(url_for("volunteer.dashboard", group_id=group_id, view="users"))

    except Exception as e:
        app_logger.exception("Error approving user %s in group %s by user %s: %s", user_id, group_id, session.get("user_id"), str(e))
        abort(500)

@volunteer.route("/dashboard/<int:group_id>/remove_user/<int:user_id>", methods=["POST"])
@role_required(2)
@limiter.limit("1/second;20/hour;60/day")
def remove_user(group_id, user_id):
    try:
        current_user_id = session.get("user_id")
        if not current_user_id:
            app_logger.warning("Unauthenticated attempt to remove user %s from group %s", user_id, group_id)
            return redirect(url_for("login"))

        group = db.get_group_by_id(group_id)
        if not group:
            app_logger.warning("Attempt to remove user %s from non-existent group %s by user %s", user_id, group_id, current_user_id)
            abort(404)

        if group.get("owner") != current_user_id:
            app_logger.warning("User %s tried to remove user %s from unauthorized group %s", current_user_id, user_id, group_id)
            abort(403)

        db.remove_user_from_group(user_id, group_id)
        flash("User removed from group.", "warning")
        return redirect(url_for("volunteer.dashboard", group_id=group_id, view="users"))

    except Exception as e:
        app_logger.exception("Error removing user %s from group %s by user %s: %s", user_id, group_id, session.get("user_id"), str(e))
        abort(500)

@volunteer.route("/dashboard/<int:group_id>/remove_activity/<int:activity_id>", methods=["POST"])
@role_required(2)
def remove_activity(group_id, activity_id):
    try:
        user_id = session.get("user_id")
        if not user_id:
            app_logger.warning("Unauthenticated user attempted to remove activity %s from group %s", activity_id, group_id)
            return redirect(url_for("login"))

        group = db.get_group_by_id(group_id)
        if not group:
            app_logger.warning("Attempt to remove activity %s from non-existent group %s by user %s", activity_id, group_id, user_id)
            abort(404)

        if group.get("owner") != user_id:
            app_logger.warning("User %s attempted to remove activity %s from group %s they do not own", user_id, activity_id, group_id)
            abort(403)

        activity = db.get_activity_by_id(activity_id)
        if not activity or activity.get("group_id") != group_id:
            app_logger.warning("User %s tried to remove mismatched or non-existent activity %s from group %s", user_id, activity_id, group_id)
            abort(404)

        db.remove_activity(activity_id)
        flash("Activity removed.", "warning")
        return redirect(url_for("volunteer.dashboard", group_id=group_id, view="activities"))

    except Exception as e:
        app_logger.exception("Unhandled error removing activity %s from group %s by user %s: %s", activity_id, group_id, user_id, str(e))
        abort(500)

@volunteer.route("/createInterestGroupProposal", methods=["GET", "POST"])
@role_required(2)
@limiter.limit("3/hour;7/day", methods=["POST"])
def create_group_proposal():
    # try:
    user_id = session.get("user_id")
    if not user_id:
        app_logger.warning("Unauthenticated user attempted to create a group proposal.")
        return redirect(url_for("login"))

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

    # except Exception as e:
    #     app_logger.exception("Unhandled error during group proposal creation by user %s: %s", user_id, str(e))
    #     abort(500)


@volunteer.route("/createActivityProposal/<int:group_id>", methods=["GET", "POST"])
@role_required(2)
@limiter.limit("5/hour;10/day", methods=["POST"])
def create_activity_proposal(group_id):
    #try:
        user_id = session.get("user_id")
        if not user_id:
            app_logger.warning("Unauthenticated user tried to access activity proposal for group %s", group_id)
            return redirect(url_for("login"))

        group = db.get_group_by_id(group_id)
        if not group:
            app_logger.warning("User %s tried to access non-existent group ID %s", user_id, group_id)
            abort(404)

        if group["owner"] != user_id:
            app_logger.warning("User %s tried to propose activity for group they do not own (%s)", user_id, group_id)
            abort(403)

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

    # except Exception as e:
    #     app_logger.exception("Unhandled exception in create_activity_proposal for group %s: %s", group_id, str(e))
    #     abort(500)

@volunteer.route('/dashboard')
@role_required(2)
def volunteer_dashboard_groups():
    try:
        user_id = session.get('user_id')
        if not user_id:
            app_logger.warning("Unauthenticated user tried to access volunteer dashboard")
            return redirect(url_for('login'))

        groups = db.get_groups_by_owner(user_id)
        if groups is None:
            app_logger.warning("Volunteer %s has no owned groups or database returned None", user_id)
            groups = []

        return render_template('volunteer/group_list_dashboard.html', groups=groups)

    except Exception as e:
        app_logger.exception("Exception occurred in volunteer dashboard for user %s: %s", user_id, str(e))
        abort(500)
