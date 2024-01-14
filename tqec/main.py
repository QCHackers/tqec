import json

from flask import Flask, send_file, request
from flask_cors import CORS, cross_origin

from tqec.plaquette.plaquette import PlaquetteQubit, Plaquette
from tqec.position import Position

app = Flask(__name__)
CORS(app)

@app.route("/")
def root():
    return send_file("static/index.html")


if __name__ == "__main__":
    # This is used when running locally only. When deploying to Google App
    # Engine, a webserver process such as Gunicorn will serve the app. This
    # can be configured by adding an `entrypoint` to app.yaml.
    # Flask's development server will automatically serve static files in
    # the "static" directory. See:
    # http://flask.pocoo.org/docs/1.0/quickstart/#static-files. Once deployed,
    # App Engine itself will serve those files as configured in app.yaml.
    app.run(host="127.0.0.1", port=8080, debug=True)

@app.route("/stim", methods=['GET', 'POST'])
@cross_origin(supports_credentials=True)
def jsonToStim():
    _json = request.get_json()
    if _json is None:
        return "No JSON provided", 400
    # Construct the plaquettes from the given file
    plaquettes = []
    for plaquette in _json["plaquettes"]:
        # Construct the qubits
        qubits = [PlaquetteQubit(Position(qubit["x"], qubit["y"])) for qubit in plaquette["qubits"]]
        # TODO: Construct the plaquette

    # TODO: deserialize templates, Invoke generate_circuit
    filename = "circuit.stim"
    with open(filename, "w") as f:
        json.dump(_json, f)
    return send_file(filename)