from flask import Flask, request, jsonify, render_template
from pymongo import MongoClient
from datetime import datetime
import config

app = Flask(__name__)
client = MongoClient(config.MONGO_URI)
db = client.webhookdb
collection = db.githubEvents

@app.route('/webhook', methods=['POST'])
def webhook():
    payload = request.json
    event_type = request.headers.get("X-GitHub-Event")
    sender = payload.get("sender", {}).get("login", "unknown")
    timestamp = datetime.utcnow().strftime("%d %B %Y - %H:%M %p UTC")

    if event_type == "push":
        data = {
            "request_id": payload.get("after"),
            "author": sender,
            "action": "PUSH",
            "from_branch": payload.get("ref").split("/")[-1],
            "to_branch": "",
            "timestamp": timestamp
        }
    elif event_type == "pull_request":
        pr = payload.get("pull_request", {})
        if payload.get("action") == "opened":
            data = {
                "request_id": str(pr.get("id")),
                "author": sender,
                "action": "PULL_REQUEST",
                "from_branch": pr.get("head", {}).get("ref"),
                "to_branch": pr.get("base", {}).get("ref"),
                "timestamp": timestamp
            }
        elif payload.get("action") == "closed" and pr.get("merged"):
            data = {
                "request_id": str(pr.get("id")),
                "author": sender,
                "action": "MERGE",
                "from_branch": pr.get("head", {}).get("ref"),
                "to_branch": pr.get("base", {}).get("ref"),
                "timestamp": timestamp
            }
        else:
            return jsonify({"status": "ignored"}), 200
    else:
        return jsonify({"status": "ignored"}), 200

    collection.insert_one(data)
    return jsonify({"status": "stored"}), 200

@app.route('/')
def index():
    events = collection.find().sort("timestamp", -1)
    return render_template("index.html", data=events)

if __name__ == '__main__':
    app.run(port=5000, debug=True)