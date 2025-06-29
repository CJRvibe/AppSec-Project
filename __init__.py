from flask import Flask, render_template, redirect, url_for, request
from forms import InterestGroupProposalForm

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("home.html")

@app.route('/login')
def login():
    return render_template('login.html')

@app.route('/signUp')
def register():
    return render_template('sign_up.html')

@app.route('/forgetPassword')
def forget_password():
    return render_template('forget_password.html')

@app.route('/enterPin')
def enter_pin():
    return render_template('enter_pin.html')

@app.route('/changePassword')
def change_password():
    return render_template('change_password.html')


@app.route('/activity-hub')
def activity_hub():
    activities = [
        {"category": "Music & Vocal", "name": "Karaoke", "image": "/static/img/karaoke.jpg"}
    ]
    return render_template('/activity_hub.html', activities=activities)


@app.route("/createInterestGroupProposal", methods=["GET", "POST"])
def create_group_proposal():
    proposal_form = InterestGroupProposalForm(request.form)
    if request.method == "POST" and proposal_form.validate():
        return redirect(url_for("index"))
    return render_template("create_interest_group_proposal.html", form=proposal_form)


if __name__ == "__main__":
    app.run()