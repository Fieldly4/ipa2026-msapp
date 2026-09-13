import os

from flask import Flask, request, render_template, redirect, url_for
from pymongo import MongoClient
from bson.objectid import ObjectId

app = Flask(__name__)

# 1. เชื่อมต่อ MongoDB
mongo_uri  = os.environ.get("MONGO_URI", "mongodb://mongo:27017/")
db_name    = os.environ.get("DB_NAME", "router_db")

client = MongoClient(mongo_uri)
db = client[db_name]

# ประกาศ Collections ให้ครบถ้วน
comments_col = db["routers"]
results_collection = db["router_results"]   # <-- เพิ่มบรรทัดนี้

@app.route("/")
def main():
    data = list(comments_col.find())
    return render_template("index.html", data=data)

@app.route("/add", methods=["POST"])
def add_comment():
    ip = request.form.get("IP")
    username = request.form.get("username")
    password = request.form.get("password")

    if ip and username and password:
        comments_col.insert_one({
            "ip": ip,
            "username": username,
            "password": password
        })
    return redirect(url_for("main"))

@app.route("/router/<router_ip>")
def router_detail(router_ip):
    history_records = list(
        results_collection.find({"router_ip": router_ip})
        .sort("timestamp", -1)
        .limit(3)
    )

    return render_template(
        "router_detail.html",
        router_ip=router_ip,
        records=history_records
    )

@app.route("/delete/<comment_id>", methods=["POST"])
def delete_comment(comment_id):
    try:
        comments_col.delete_one({"_id": ObjectId(comment_id)})
    except Exception:
        pass
    return redirect(url_for("main"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
