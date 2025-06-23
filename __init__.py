from flask import Flask, render_template, redirect, url_for, request
from forms import InterestGroupProposalForm

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("home.html")


@app.route("/createInterestGroupProposal", methods=["GET", "POST"])
def create_group_proposal():
    proposal_form = InterestGroupProposalForm(request.form)
    if request.method == "POST" and proposal_form.validate():
        return redirect(url_for("index"))
    return render_template("create_interest_group_proposal.html", form=proposal_form)


if __name__ == "__main__":
    app.run()