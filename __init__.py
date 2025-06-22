from flask import Flask, render_template, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("home.html")

@app.route('/activity-hub')
def activity_hub():
    activities = [
        {"category": "Music & Vocal", "name": "Karaoke", "image": "/static/img/karaoke.jpg"}
    ]
    return render_template('/activity_hub.html', activities=activities)


if __name__ == "__main__":
    app.run()