import datetime

from flask import Flask, render_template, send_file
from flask_cors import CORS, cross_origin

app = Flask(__name__)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['CORS_RESOURCES'] = {r"/stim": {"origins": "*"}}

@app.route("/")
def root():
    dummy_times = [datetime.datetime.now()]
    return render_template("index.html", times=dummy_times)


if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)

@app.route("/stim", methods=['GET'])
@cross_origin(supports_credentials=True)
def pdf():
    return send_file("teleportation.stim")