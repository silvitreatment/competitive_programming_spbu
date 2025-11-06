from flask import Flask, request 
from markupsafe import escape
app = Flask(__name__)

@app.route("/", methods=["GET"])
def hello():

    name = request.args.get("name", "Recruto")
    message = request.args.get("message", "Давай дружить")

    name = escape(name)
    message = escape(message)

    return f"Hello {name}! {message}!"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5050)