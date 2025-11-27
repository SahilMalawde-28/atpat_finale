from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
import csv, io, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from api.config import db
from werkzeug.security import generate_password_hash
from bson.objectid import ObjectId

flag_routes = Blueprint("flag_routes", __name__)

admins_db = db["admins"]
tests_db = db["tests"]
invites_db = db["invites"]
flags_db = db["flags"]


@flag_routes.route("/postflags", methods=["POST"])
def postflags():
    data = request.get_json()

    required_fields = [
        "mis_id", "parenturl", "start_time", "end_time",
        "no_face", "multi_face", "off_gaze", "alt_tab",
        "audio_events", "typing_events", "avg_wpm",
        "backspace_ratio", "typing_flags", "proofs"
    ]

    # ✅ Validate presence of all required fields
    for field in required_fields:
        if field not in data:
            return jsonify({"status": "error", "message": f"Missing field: {field}"}), 400

    mis_id = str(data["mis_id"])
    parenturl = data["parenturl"]

    # ✅ Find test_id from tests_db using parenturl
    test_doc = tests_db.find_one({"parenturl": parenturl})
    if not test_doc:
        return jsonify({"status": "error", "message": "Test not found for given parenturl"}), 404

    test_id = str(test_doc["_id"])

    # ✅ Prepare flag document
    flag_doc = {
        "test_id": test_id,
        "mis_id": mis_id,
        "start_time": data["start_time"],
        "parenturl": parenturl,
        "end_time": data["end_time"],
        "no_face": data["no_face"],
        "multi_face": data["multi_face"],
        "off_gaze": data["off_gaze"],
        "alt_tab": data["alt_tab"],
        "audio_events": data["audio_events"],
        "typing_events": data["typing_events"],
        "avg_wpm": data["avg_wpm"],
        "backspace_ratio": data["backspace_ratio"],
        "typing_flags": data["typing_flags"],
        "proofs": data["proofs"],
        "to_review": False
    }

    # ✅ Upsert (update existing or insert new)
    result = flags_db.update_one(
        {"test_id": test_id, "mis_id": mis_id},
        {"$set": flag_doc},
        upsert=True
    )

    if result.matched_count > 0:
        msg = "Existing flag document updated successfully."
    else:
        msg = "New flag document inserted successfully."

    return jsonify({"status": "success", "message": msg}), 200



@flag_routes.route("/getflag", methods=["POST"])
def getflag():
    data = request.get_json()
    test_id = data.get("test_id")
    print("🔍 Received test_id:", test_id)
    print("🗂️ All existing test_ids:", list(flags_db.distinct("test_id")))
    if not test_id:
        return jsonify({"status": "error", "message": "Missing test_id"}), 400

    user_session = session.get("user", {})
    role = user_session.get("role")
    mis_id = user_session.get("mis_id")

    # If student → only fetch their own document
    # If admin → fetch all students' documents for that test
    query = {"test_id": test_id}
    if role == "student":
        query["mis_id"] = mis_id  

    flags_cursor = flags_db.find(query)
    flags_list = []

    for f in flags_cursor:
        # Get student info for display
        student_info = admins_db.find_one(
            {"mis_id": f.get("mis_id")},  # ✅ fixed here
            {"_id": 0, "name": 1, "email": 1}
        )

        flag_obj = {
            "mis_id": f.get("mis_id"),
            "parenturl": f.get("parenturl"),
            "start_time": f.get("start_time"),
            "end_time": f.get("end_time"),
            "no_face": f.get("no_face"),
            "multi_face": f.get("multi_face"),
            "off_gaze": f.get("off_gaze"),
            "alt_tab": f.get("alt_tab"),
            "audio_events": f.get("audio_events"),
            "typing_events": f.get("typing_events"),
            "avg_wpm": f.get("avg_wpm"),
            "backspace_ratio": f.get("backspace_ratio"),
            "typing_flags": f.get("typing_flags"),
            "proofs": f.get("proofs", []),
            "to_review": f.get("to_review", False),
            "student_name": student_info.get("name", "Unknown") if student_info else "Unknown",
            "student_email": student_info.get("email", "Unknown") if student_info else "Unknown",
        }

        flags_list.append(flag_obj)
    print("Fetched flags:", flags_list)
    return jsonify({"status": "success", "flags": flags_list}), 200



@flag_routes.route("/updateReview", methods=["POST"])
def update_review():
    data = request.get_json()
    test_id = data.get("test_id")
    mis_id = data.get("mis_id")  # changed field name
    to_review = data.get("to_review")

    if not test_id or not mis_id or to_review is None:
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    # Update the student's flag document for this test
    result = flags_db.update_one(
        {"test_id": test_id, "mis_id": mis_id},
        {"$set": {"to_review": to_review}}
    )

    if result.modified_count == 1:
        return jsonify({"status": "success", "message": "Review status updated"}), 200
    else:
        return jsonify({"status": "error", "message": "Flag not found or no change"}), 404



@flag_routes.route("/deleteFlag", methods=["DELETE"])
def delete_flag():
    data = request.get_json()
    test_id = data.get("test_id")
    mis_id = data.get("mis_id")

    if not test_id or not mis_id:
        return jsonify({"status": "error", "message": "Missing required fields"}), 400

    result = flags_db.delete_one({"test_id": test_id, "mis_id": mis_id})

    if result.deleted_count == 1:
        return jsonify({"status": "success", "message": "Flag deleted successfully"}), 200
    else:
        return jsonify({"status": "error", "message": "Flag not found"}), 404
