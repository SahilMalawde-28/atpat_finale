from flask import Blueprint, request, jsonify, session
from werkzeug.utils import secure_filename
import csv, io, smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from api.config import db
from werkzeug.security import generate_password_hash
from bson.objectid import ObjectId

test_routes = Blueprint("test_routes", __name__)

admins_db = db["admins"]
tests_db = db["tests"]
invites_db = db["invites"]

# --- Configure SMTP ---
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SENDER_EMAIL = "atpat.invites@gmail.com"
SENDER_PASSWORD = "pvjc wsgh pbqx xjgj"  # Use Gmail App Password, NOT normal password!

@test_routes.route("/createtest", methods=["POST"])
def createtest():
    try:
        testname = request.form.get("testname")
        parenturl = request.form.get("parenturl")
        duration = request.form.get("duration")
        loginwindowstart = request.form.get("loginwindowstart")
        loginwindowend = request.form.get("loginwindowend")
        description = request.form.get("description", "")
        send_invites = int(request.form.get("send_invites", 0))

        # --- Check file ---
        if "file" not in request.files:
            return jsonify({"status": "error", "message": "CSV file missing"}), 400

        file = request.files["file"]
        if not file.filename.endswith(".csv"):
            return jsonify({"status": "error", "message": "Please upload a CSV file"}), 400

        # --- Parse CSV ---
        stream = io.StringIO(file.stream.read().decode("UTF8"))
        csv_reader = csv.DictReader(stream)

        # --- Get admin info from session ---
        admin_info = session.get("user", {
            "name": "Unknown Admin",
            "email": "unknown@example.com",
            "mis_id": "N/A",
            "role": "admin"
        })

        # --- Initialize student list ---
        students_list = []

        # --- Create Test Document FIRST ---
        test_doc = {
            "name": testname,
            "parenturl": parenturl,
            "duration_minutes": duration,
            "login_window_start": loginwindowstart,
            "login_window_end": loginwindowend,
            "created_at": datetime.utcnow(),
            "students": students_list,
            "instructions": description,
            "admin_info": admin_info
        }
        test_id = tests_db.insert_one(test_doc).inserted_id

        # --- Optional: Prepare SMTP connection ---
        smtp_server = None
        if send_invites == 1:
            smtp_server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            smtp_server.starttls()
            smtp_server.login(SENDER_EMAIL, SENDER_PASSWORD)

        # --- Process each row in CSV ---
        for row in csv_reader:
            row = {k.strip(): (v.strip() if v else v) for k, v in row.items()}
            name = row.get("name")
            email = row.get("email")
            mis_id = row.get("mis_id")

            if not name or not email or not mis_id:
                continue

            students_list.append(mis_id)

            # 1️⃣ Ensure student exists
            existing = admins_db.find_one({"mis_id": mis_id})
            if not existing:
                result = admins_db.insert_one({
                    "name": name,
                    "email": email,
                    "mis_id": mis_id,
                    "roles": ["student"],
                    "tests_registered": [{
                        "testname": testname,
                        "parenturl": parenturl
                    }],
                    "hashed_password": generate_password_hash("1234")
                })
                student_id = result.inserted_id
            else:
                admins_db.update_one(
                    {"mis_id": mis_id},
                    {"$addToSet": {
                        "tests_registered": {
                            "testname": testname,
                            "parenturl": parenturl
                        }
                    }}
                )
                student_id = existing["_id"]

            # 2️⃣ Create unique link
            unique_link = f"{parenturl}?ATPAT={mis_id}"

            # 3️⃣ Insert into invites collection
            invites_db.insert_one({
                "test_id": test_id,
                "student_id": student_id,
                "mis_id": mis_id,
                "invite_link": unique_link,
                "sent_at": datetime.utcnow(),
                "status": "pending"
            })

            # 4️⃣ Send email if required
            if send_invites == 1:
                subject = f"Invitation to {testname}"
                body = f"""
Hi {name},

You have been invited to take the test **{testname}**.

🕒 Duration: {duration} minutes  
📅 Login window: {loginwindowstart} → {loginwindowend}

Please use your personal test link to start the test:
{unique_link}

Notes: {description}

Best regards,  
ATPAT Admin
                """
                msg = MIMEMultipart()
                msg["From"] = SENDER_EMAIL
                msg["To"] = email
                msg["Subject"] = subject
                msg.attach(MIMEText(body, "plain"))
                smtp_server.sendmail(SENDER_EMAIL, email, msg.as_string())

        # --- Close SMTP connection if used ---
        if smtp_server:
            smtp_server.quit()

        # --- Update test doc with full student list ---
        tests_db.update_one({"_id": test_id}, {"$set": {"students": students_list}})

        return jsonify({
            "status": "success",
            "message": f"Test '{testname}' created successfully with invites."
        }), 201

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@test_routes.route("/showtestsadmin", methods=["GET"])
def showtestsadmin():
    try:
        user = session.get("user")
        if not user or user.get("role") != "admin":
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        admin_email = user["email"]

        tests = list(tests_db.find(
            {"admin_info.email": admin_email},
            {
                "_id": 1,  # we will convert this to 'id'
                "name": 1,
                "parenturl": 1,
                "login_window_start": 1,
                "login_window_end": 1,
            }
        ))

        # Convert _id to string for frontend
        for test in tests:
            test["id"] = str(test["_id"])
            del test["_id"]

        return jsonify({"status": "success", "tests": tests}), 200
    except Exception as e:
        print("Error in /showtestsadmin:", e)
        return jsonify({"status": "error", "message": str(e)}), 500



@test_routes.route("/showtestsstudents", methods=["GET"])
def showtestsstudents():
    try:
        user = session.get("user")
        if not user or user.get("role") != "student":
            return jsonify({"status": "error", "message": "Unauthorized"}), 401

        student_email = user["email"]

        # Step 1: Fetch student's registered tests
        student_doc = admins_db.find_one(
            {"email": student_email},
            {"_id": 0, "tests_registered": 1}
        )

        if not student_doc or not student_doc.get("tests_registered"):
            return jsonify({"status": "success", "tests": []}), 200

        registered_tests = student_doc["tests_registered"]
        enriched_tests = []

        # Step 2: For each registered test, fetch login window + ID from tests_db
        for test in registered_tests:
            testname = test.get("testname")
            parenturl = test.get("parenturl")

            test_doc = tests_db.find_one(
                {"name": testname, "parenturl": parenturl},
                {"_id": 1, "login_window_start": 1, "login_window_end": 1}
            )

            if test_doc:
                enriched_tests.append({
                    "name": testname,
                    "parenturl": parenturl,
                    "id": str(test_doc["_id"]),  # include ID
                    "login_window_start": test_doc.get("login_window_start"),
                    "login_window_end": test_doc.get("login_window_end")
                })
            else:
                enriched_tests.append({
                    "name": testname,
                    "parenturl": parenturl,
                    "id": None,
                    "login_window_start": None,
                    "login_window_end": None
                })

        return jsonify({"status": "success", "tests": enriched_tests}), 200

    except Exception as e:
        print("Error in /showtestsstudents:", e)
        return jsonify({"status": "error", "message": str(e)}), 500