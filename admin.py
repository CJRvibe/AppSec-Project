from flask import Flask, render_template, redirect, url_for, request, abort, session, Blueprint
import db

admin = Blueprint("admin", __name__, template_folder="templates")


@admin.route("/interestGroups/proposals")
def manage_group_proposals():
    groups = db.admin_get_groups(type="pending")

    return render_template("admin/manage_groups.html", groups=groups, type="pending")


@admin.route("/interestGroups")
def manage_active_groups():
    groups = db.admin_get_groups()

    return render_template("admin/manage_groups.html", groups=groups, type="approved")


@admin.route("/interestGroups/rejectedGroups")
def manage_reject_groups():
    groups = db.admin_get_groups(type="rejected")

    return render_template("admin/manage_groups.html", groups=groups, type="rejected")


@admin.route("/interestGroups/<int:id>")
def view_group(id):
    group = db.admin_get_group_by_id(id)
    if group:
        return render_template("admin/view_group.html", group=group)
    else:
        abort(404, description="Group not found")


@admin.route("/interestGroups/approveGroupProposal/<int:id>", methods=["POST"])
def approve_group_proposal(id):
    group = db.admin_get_group_by_id(id)

    if group and group.get("status") == "pending":
        db.admin_update_group_proposal(id, approved=True)
        return redirect(url_for(".manage_active_groups"))
    elif group and group.get("status") != "pending":
        abort(405, description="Method not allowed for this group")
    else:
        abort(404, description="Group not found")


@admin.route("/interestGroups/rejectGroupProposal/<int:id>", methods=["POST"])
def reject_group_proposal(id):
    group = db.admin_get_group_by_id(id)

    if group and group.get("status") == "pending":
        db.admin_update_group_proposal(id, approved=False)
        return redirect(url_for(".manage_reject_groups"))
    elif group and group.get("status") != "pending":
        abort(405, description="Method not allowed for this group")
    else:
        abort(404, description="Group not found")


@admin.route("/groupActivities")
def manage_approved_activities():
    activities = db.admin_get_group_activities(type="approved")

    return render_template("admin/manage_activities.html", activities=activities, type="approved")


@admin.route("/groupActivities/activityProposals")
def manage_pending_activities():
    activities = db.admin_get_group_activities(type="pending")

    return render_template("admin/manage_activities.html", activities=activities, type="pending")


@admin.route("/gropupActivities/rejectedActivities")
def manage_rejected_activities():
    activities = db.admin_get_group_activities(type="rejected")

    return render_template("admin/manage_activities.html", activities=activities, type="rejected")


@admin.route("/groupActivities/<int:id>")
def view_activity(id):
    activity = db.admin_get_group_activity(id)

    if activity:
        return render_template("admin/view_activity.html", activity=activity)
    else: abort(404, description="Activity not found")


@admin.route("/groupActivities/approveActivity/<int:id>", methods=["POST"])
def approve_activity(id):
    activity = db.get_activity_by_id(id)

    if activity and activity.get("status") == "pending":
        db.admin_update_activity_proposal(id, approved=True)
        return redirect(url_for(".manage_approved_activities"))
    elif activity and activity.get("status") != "pending":
        abort(405, description="Method not allowed for this activity")
    else: abort(404, description="Activity not found")


@admin.route("/groupActivities/rejectActivity/<int:id>", methods=["POST"])
def reject_activity(id):
    activity = db.get_activity_by_id(id)

    if activity and activity.get("status") == "pending":
        db.admin_update_activity_proposal(id, approved=False)
        return redirect(url_for(".manage_approved_activities"))
    elif activity and activity.get("status") != "pending":
        abort(405, description="Method not allowed for this activity")
    else: abort(404, description="Activity not found")