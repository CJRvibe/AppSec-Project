from flask import Flask, render_template, redirect, url_for, request, abort, session, Blueprint
import db

admin = Blueprint("admin", __name__, template_folder="templates")


@admin.route("/manageInterestGroupProposals")
def manage_group_proposals():
    proposals = db.get_group_proposals()

    return render_template("admin/manage_group_proposals.html", proposals=proposals)


@admin.route("/manageActiveGroups")
def manage_active_groups():
    groups = db.get_active_groups()

    return render_template("admin/manage_active_groups.html", groups=groups)


@admin.route("/viewGroupProposal/<int:id>")
def view_group_proposal(id):
    proposal = db.get_group_proposal(id)
    print(proposal)
    if proposal:
        return render_template("admin/view_group_proposal.html", proposal=proposal)
    
    session["view_error"] = id
    return redirect(url_for(".manage_group_proposals"))


@admin.route("/approveGroupProposal/<int:id>", methods=["POST"])
def approve_group_proposal(id):
    db.update_group_proposal(id, approved=True)
    
    return redirect(url_for(".manage_group_proposals"))


@admin.route("/rejectGroupProposal/<int:id>", methods=["POST"])
def reject_group_proposal(id):
    db.update_group_proposal(id, approved=False)
    
    return redirect(url_for(".manage_group_proposals"))