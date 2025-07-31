from flask import Blueprint, render_template, redirect, url_for, session, request, abort, flash
from forms import *
import json
import db

from access_control import role_required

volunteer = Blueprint("volunteer", __name__, template_folder="templates")

@volunteer.route('/dashboard/<int:group_id>')
@role_required(2)
def dashboard(group_id):
    user_id = session.get("user_id")
    group = db.get_group_by_id(group_id)

    if group["owner"] != user_id:
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



@volunteer.route("/dashboard/<int:group_id>/approve_user/<int:user_id>", methods=["POST"])
@role_required(2)
def approve_user(group_id, user_id):
    user = session.get("user_id")
    group = db.get_group_by_id(group_id)
    if not group or group["owner"] != user:
        abort(403)

    db.approve_user(user_id, group_id)
    flash("User approved.", "success")
    return redirect(url_for("volunteer.dashboard", group_id=group_id, view="users"))

@volunteer.route("/dashboard/<int:group_id>/remove_user/<int:user_id>", methods=["POST"])
@role_required(2)
def remove_user(group_id, user_id):
    user = session.get("user_id")
    group = db.get_group_by_id(group_id)
    if not group or group["owner"] != user:
        abort(403)

    db.remove_user_from_group(user_id, group_id)
    flash("User removed from group.", "warning")
    return redirect(url_for("volunteer.dashboard", group_id=group_id, view="users"))

@volunteer.route("/dashboard/<int:group_id>/remove_activity/<int:activity_id>", methods=["POST"])
@role_required(2)
def remove_activity(group_id, activity_id):
    user = session.get("user_id")
    group = db.get_group_by_id(group_id)
    if not group or group["owner"] != user:
        abort(403)

    db.remove_activity(activity_id)
    flash("Activity removed.", "warning")
    return redirect(url_for("volunteer.dashboard", group_id=group_id, view="activities"))

@volunteer.route("/createInterestGroupProposal", methods=["GET", "POST"])
@role_required(2)
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


@volunteer.route("/createActivityProposal", methods=["GET", "POST"])
@role_required(2)
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

@volunteer.route('/dashboard')
@role_required(2)
def volunteer_dashboard_groups():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    groups = db.get_groups_by_owner(user_id)

    return render_template('volunteer/group_list_dashboard.html', groups=groups)
