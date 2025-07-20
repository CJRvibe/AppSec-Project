from flask import Flask, render_template, redirect, url_for, request, abort, session, Blueprint
import db

admin = Blueprint("admin", __name__, template_folder="templates")


@admin.route("/interestGroups/proposals")
def manage_group_proposals():
    proposals = db.get_group_proposals()

    return render_template("admin/manage_group_proposals.html", proposals=proposals)


@admin.route("/interestGroups")
def manage_active_groups():
    groups = db.get_active_groups()

    return render_template("admin/manage_active_groups.html", groups=groups)


@admin.route("/interestGroups/rejectedGroups")
def manage_reject_groups():
    groups = db.get_reject_groups()

    return render_template("admin/manage_reject_groups.html", groups=groups)


@admin.route("/interestGroups/proposals/<int:id>")
def view_group_proposal(id):
    proposal = db.get_group_proposal(id)
    print(proposal)
    if proposal:
        return render_template("admin/view_group_proposal.html", proposal=proposal)
    
    session["view_error"] = id
    return redirect(url_for(".manage_group_proposals"))


@admin.route("/interestGroups/approveGroupProposal/<int:id>", methods=["POST"])
def approve_group_proposal(id):
    db.update_group_proposal(id, approved=True)
    
    return redirect(url_for(".manage_group_proposals"))


@admin.route("/interestGroups/rejectGroupProposal/<int:id>", methods=["POST"])
def reject_group_proposal(id):
    db.update_group_proposal(id, approved=False)
    
    return redirect(url_for(".manage_group_proposals"))


@admin.route("/groupActivities")
def manage_approved_activities():
    activities = db.get_group_activities(type="approved")

    return render_template("admin/manage_activities.html", activities=activities)


@admin.route("/groupActivities/activityProposals")
def manage_pending_activities():
    activities = db.get_group_activities(type="pending")

    return render_template("admin/manage_activities.html", activities=activities, type="pending")


@admin.route("/gropupActivities/rejectedActivities")
def manage_rejected_activities():
    activities = db.get_group_activities(type="rejected")

    return render_template("admin/manage_activities.html", activities=activities, type="rejected")


@admin.route("/groupActivities/<int:id>")
def view_activity(id):
    activity = db.admin_get_group_activity(id)

    return render_template("admin/view_activity.html", activity=activity)


@admin.route("/groupActivities/approveActivity/<int:id>", methods=["POST"])
def approve_activity(id):
    db.update_activity_proposal(id, approved=True)

    return redirect(url_for(".manage_approved_activities"))


@admin.route("/groupActivities/rejectActivity/<int:id>", methods=["POST"])
def reject_activity(id):
    db.update_activity_proposal(id, approved=False)

    return redirect(url_for(".manage_rejected_activities"))