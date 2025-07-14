from flask import Flask, render_template, redirect, url_for, request, abort, Blueprint
import db

admin = Blueprint("admin", __name__, template_folder="templates")


@admin.route("/manageInterestGroupProposals")
def manage_group_proposals():
    proposals = db.get_group_proposals()

    return render_template("admin/manage_group_proposals.html", proposals=proposals)