# Core & Environment
import os
import uuid
from datetime import datetime

from dotenv import load_dotenv
load_dotenv()

from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet


from dotenv import load_dotenv
load_dotenv()  # MUST be before using env vars

# Flask & Extensions
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session,
    jsonify,
    send_file
)
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash

# Database
from db import get_db_connection

# Utilities
from functools import wraps
import pytz
import requests

# Visualization
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# PDF Generation
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    Paragraph,
    Table,
    TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet


ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

def allowed_file(filename):
    return (
        "." in filename and
        filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )

import psycopg2
from psycopg2.extras import RealDictCursor
from flask import request, redirect, url_for, flash, session

RESERVED_USERNAMES = {
    "admin",
    "support",
    "root",
    "system",
    "cardiosense",
    "moderator",
    "help",
    "contact"
}

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

if not app.config["SECRET_KEY"]:
    raise RuntimeError("SECRET_KEY is missing. Set it in .env")

csrf = CSRFProtect(app)

from flask_wtf.csrf import CSRFError

@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    flash("Session expired. Please try again.", "warning")
    return redirect(url_for("login"))


UPLOAD_FOLDER = "uploads/certificates"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")

app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:root@localhost/rppg_db'

db = SQLAlchemy(app)

class HeartRateRecord(db.Model):
    __tablename__ = 'heart_rate_records'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    bpm = db.Column(db.Integer, nullable=False)
    aqi = db.Column(db.Integer)
    stress_level = db.Column(db.String(50))
    impact_category = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
   
AQICN_API_TOKEN = os.getenv("AQICN_API_TOKEN")

@csrf.exempt
@app.route("/api/stress/save", methods=["POST"])
def save_stress():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO stress_assessment (
            user_id, total_score, stress_level,
            emotional, control, resilience, cognitive, anger,
            insight_present, insight_past
        )
        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        ON CONFLICT (user_id)
        DO UPDATE SET
            total_score = EXCLUDED.total_score,
            stress_level = EXCLUDED.stress_level,
            emotional = EXCLUDED.emotional,
            control = EXCLUDED.control,
            resilience = EXCLUDED.resilience,
            cognitive = EXCLUDED.cognitive,
            anger = EXCLUDED.anger,
            insight_present = EXCLUDED.insight_present,
            insight_past = EXCLUDED.insight_past,
            updated_at = CURRENT_TIMESTAMP
    """, (
        session["user_id"],
        data["total"],
        data["level"],
        data["emotional"],
        data["control"],
        data["resilience"],
        data["cognitive"],
        data["anger"],
        data["insight_present"],
        data["insight_past"]
    ))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "ok"})


QUIZ_QUESTIONS = [
    {
        "id": 1,
        "question": "Nut consumption helps improve blood lipid levels.",
        "correct": True,
        "category": "Diet"
    },
    {
        "id": 2,
        "question": "A resting heart rate above 100 BPM is always normal.",
        "correct": False,
        "category": "Heart"
    },
    {
        "id": 3,
        "question": "Chronic stress can increase heart disease risk.",
        "correct": True,
        "category": "Stress"
    },
    {
        "id": 4,
        "question": "Poor sleep has no effect on heart rate variability.",
        "correct": False,
        "category": "Sleep"
    }
]

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)

    gender = db.Column(db.String(10))

    role = db.Column(db.String(10), default="user")  # user | coach | admin
    verification_status = db.Column(db.String(10), default="approved")
    certificate_path = db.Column(db.Text)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
 
    
with app.app_context():
    db.create_all()


@app.route('/feedback', methods=['GET', 'POST'])
def feedback():

    if 'user_id' not in session:
        flash("Please login to submit feedback.", "warning")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cur = conn.cursor()  # RealDictCursor


    cur.execute(
        "SELECT username, email FROM users WHERE id = %s",
        (session['user_id'],)
    )
    user = cur.fetchone()

    if not user:
        flash("User not found.", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        cur.execute("""
            INSERT INTO feedback (user_id, name, email, feedback_type, rating, message)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            session['user_id'],
            user["username"],
            user["email"],
            request.form.get("type"),
            request.form.get("rating"),
            request.form.get("message")
        ))

        conn.commit()
        flash("Thank you! Your feedback has been submitted successfully.", "success")
        return redirect(url_for('feedback'))

    cur.close()
    conn.close()

    return render_template(
    'feedback.html',
    user_name=user["username"],
    user_email=user["email"]
    )


@app.route("/api/last-health-summary")
def last_health_summary():
    user_id = request.args.get("user_id") or session.get("user_id")

    if not user_id:
        return jsonify({"exists": False}), 401

    record = (
        HeartRateRecord.query
        .filter_by(user_id=user_id)
        .order_by(HeartRateRecord.created_at.desc())
        .first()
    )

    if not record:
        return jsonify({"exists": False})

    return jsonify({
        "exists": True,
        "bpm": record.bpm,
        "impactCategory": record.impact_category,
        "message": f"{record.stress_level or 'Normal'} stress level detected",
        "timestamp": record.created_at.isoformat()
    })
    
@app.route("/api/coaches")
def get_coaches():
    if "user_id" not in session:
        return jsonify([]), 401

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT id, username
        FROM users
        WHERE role = 'coach'
          AND verification_status = 'approved'
        ORDER BY username
    """)

    coaches = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(coaches)

@csrf.exempt
@app.route("/api/telehealth/request", methods=["POST"])
def submit_consultation():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO consultation_requests (user_id, coach_id, reason, details)
        VALUES (%s, %s, %s, %s)
    """, (
        session["user_id"],
        data["coach_id"],
        data["reason"],
        data.get("details", "")
    ))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"success": True})

@app.route("/api/coach/requests")
def coach_requests():
    if "user_id" not in session:
        return jsonify([])

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            cr.id,
            cr.user_id AS patient_id,
            u.username AS patient,
            cr.reason,
            cr.details,
            cr.created_at
        FROM consultation_requests cr
        JOIN users u ON u.id = cr.user_id
        WHERE cr.coach_id = %s
        ORDER BY cr.created_at DESC
    """, (session["user_id"],))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(rows)


@app.route("/api/telehealth/user-snapshot/<int:user_id>")
def telehealth_user_snapshot(user_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT role FROM users WHERE id=%s", (session["user_id"],))
    role = cur.fetchone()
    if not role or role["role"] != "coach":
        cur.close()
        conn.close()
        return jsonify({"error": "Forbidden"}), 403

    cur.execute("SELECT username FROM users WHERE id=%s", (user_id,))
    user = cur.fetchone()

    cur.execute("""
        SELECT bpm, created_at
        FROM heart_rate_records
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 7
    """, (user_id,))
    hr_rows = cur.fetchall()

    cur.execute("""
        SELECT total_score, stress_level, updated_at
        FROM stress_assessment
        WHERE user_id = %s
        ORDER BY updated_at DESC
        LIMIT 1
    """, (user_id,))
    stress = cur.fetchone()

    cur.close()
    conn.close()

    bpm_values = [r["bpm"] for r in hr_rows]

    return jsonify({
        "username": user["username"],
        "heart_rate": {
            "avg": round(sum(bpm_values) / len(bpm_values)) if bpm_values else None,
            "max": max(bpm_values) if bpm_values else None,
            "min": min(bpm_values) if bpm_values else None,
            "history": [
                {
                    "bpm": r["bpm"],
                    "time": r["created_at"].strftime("%d %b %Y %I:%M %p")
                } for r in hr_rows[::-1]
            ]
        },
        "stress": stress
    })


@app.route('/all-topics')
def all_topics():
    return render_template('all-topics.html') 

@app.route('/all-articles')
def all_articles():
    return render_template('all-articles.html')   

@app.route('/how_to_use_heart_rate.html')
def help_page():
    return render_template('how_to_use_heart_rate.html')

# Route for Low-Salt Diet Page
@app.route('/diet-low-salt.html')
def diet_low_salt():
    return render_template('diet-low-salt.html')

# Route for High Protein Diet
@app.route('/diet-high-protein.html')
def diet_high_protein():
    return render_template('diet-high-protein.html')

# Route for Omega-3 Diet
@app.route('/diet-omega-3.html')
def diet_omega_3():
    return render_template('diet-omega-3.html')

# Route for Resting Heart Rate Article
@app.route('/article/resting-heart-rate')
def article_resting_hr():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('article_resting_hr.html')

# Route for Heart Healthy Diet Article
@app.route('/article/heart-healthy-diet')
def article_diet():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('article_diet.html')

@app.route('/article/heart-disease')
def article_heart_disease():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('article_heart_disease.html')

@app.route('/article/stress-connection')
def stress_article_page():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('article_stress.html')

@app.route('/heart-health')
def heart_health_hub():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('heart.html')

@app.route("/api/telehealth/coach-response")
def telehealth_coach_response():
    if "user_id" not in session:
        return jsonify({"note": None}), 401

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            cn.note,
            cn.created_at,
            u.username AS coach_name,
            u.email AS coach_email
        FROM coach_notes cn
        JOIN users u ON u.id = cn.coach_id
        WHERE cn.user_id = %s
        ORDER BY cn.created_at DESC
        LIMIT 1
    """, (session["user_id"],))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({"note": None})

    return jsonify({
        "note": row["note"],
        "coach_name": row["coach_name"],
        "coach_email": row["coach_email"],
        "timestamp": row["created_at"].isoformat()
    })

@app.route('/report')
def report():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    print("REPORT USER:", session.get("username"))  

    return render_template(
        'report.html',
        username=session.get("username")
    )

@app.route("/api/telehealth/coach-timeline")
def telehealth_coach_timeline():
    if "user_id" not in session:
        return jsonify([]), 401

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            cn.id,
            cn.note,
            cn.created_at,
            cn.seen,
            u.username AS coach_name,
            u.email AS coach_email
        FROM coach_notes cn
        JOIN users u ON u.id = cn.coach_id
        WHERE cn.user_id = %s
        ORDER BY cn.created_at DESC
    """, (session["user_id"],))

    rows = cur.fetchall()
    cur.close()
    conn.close()

    timeline = []
    for r in rows:
        timeline.append({
            "id": r["id"],
            "note": r["note"],
            "coach_name": r["coach_name"],
            "coach_email": r["coach_email"],
            "timestamp": r["created_at"].isoformat(),
            "seen": r["seen"]
        })


    return jsonify(timeline)

@csrf.exempt
@app.route("/api/telehealth/mark-seen", methods=["POST"])
def mark_coach_note_seen():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    note_id = request.json.get("note_id")
    if not note_id:
        return jsonify({"error": "Invalid data"}), 400

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        UPDATE coach_notes
        SET seen = TRUE
        WHERE id = %s AND user_id = %s
    """, (note_id, session["user_id"]))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "seen"})


@app.route('/heart-rate')
def heart_rate():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('heart_rate.html')


@app.route('/physical-health')
def physical_health():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('physical_health.html')

def calculate_bmi(weight, height_cm):
    height_m = height_cm / 100
    return round(weight / (height_m ** 2), 2)


def calculate_wasi(age, weight, height_cm):
    bmi = calculate_bmi(weight, height_cm)

    if bmi < 18.5:
        bmi_score = 50
    elif bmi <= 24.9:
        bmi_score = 100
    elif bmi <= 29.9:
        bmi_score = 70
    else:
        bmi_score = 40

    age_factor = max(0.7, 1 - (age - 20) * 0.005)
    wasi = round(bmi_score * age_factor, 1)

    return wasi


def calculate_mls(age, weight, height_cm):
    height_m = height_cm / 100
    ideal_weight = 22 * (height_m ** 2)

    load_ratio = weight / ideal_weight

    if age < 30:
        age_multiplier = 1.0
    elif age < 45:
        age_multiplier = 1.1
    else:
        age_multiplier = 1.2

    mls = round(load_ratio * age_multiplier * 100, 1)
    return mls

@app.route("/api/stress/latest")
def get_latest_stress():
    if "user_id" not in session:
        return jsonify({}), 401

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            total_score,
            stress_level,
            emotional,
            control,
            resilience,
            cognitive,
            anger,
            insight_past,
            updated_at
        FROM stress_assessment
        WHERE user_id = %s
        ORDER BY updated_at DESC
        LIMIT 1
    """, (session["user_id"],))

    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({})

    row["measured_at"] = row["updated_at"].isoformat()

    return jsonify(row)




@app.route("/stress-check")
def stress_check():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("stress_check.html")

@app.route("/add-plan")
def add_plan():
    return render_template("add_plan.html")

@csrf.exempt
@app.route("/api/quiz", methods=["POST"])
def quiz():
    data = request.json
    correct = data["answer"] is True
    return jsonify({"correct": correct})


@app.route("/mental-health-report")
def mental_health_report():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("mental_health_report.html")


@app.route('/lifestyle')
def lifestyle():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('lifestyle.html')



@app.route('/telehealth')
def telehealth():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template('telehealth.html')


@app.route("/coach/dashboard")
def coach_dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT id, role, verification_status FROM users WHERE id = %s",
        (session["user_id"],)
    )
    coach = cur.fetchone()

    if not coach or coach["role"] != "coach":
        cur.close()
        conn.close()
        return redirect(url_for("index"))

    if coach["verification_status"] != "approved":
        cur.close()
        conn.close()
        return redirect(url_for("coach_pending"))

    cur.execute("""
        SELECT id, username, gender
        FROM users
        WHERE role = 'user'
        ORDER BY id DESC
    """)
    patients = cur.fetchall()

    selected_patient = patients[0] if patients else None

    metrics = None
    notes = []

    if selected_patient:
        cur.execute("""
            SELECT avg_bpm, stress_level, mls
            FROM health_metrics
            WHERE user_id = %s
            ORDER BY created_at DESC
            LIMIT 1
        """, (selected_patient["id"],))
        metrics = cur.fetchone()

        cur.execute("""
            SELECT note, created_at
            FROM coach_notes
            WHERE user_id = %s
            ORDER BY created_at DESC
        """, (selected_patient["id"],))
        notes = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "coach_dashboard.html",
        coach=coach,
        patients=patients,
        selected_patient=selected_patient,
        metrics=metrics,
        notes=notes
    )


@app.route("/coach/pending")
def coach_pending():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("coach_pending.html")


@app.route('/eye_health')
def eye_health():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template('eye_health.html')


@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    gender = request.form.get('gender')

    user = db.session.get(User, session['user_id'])

    if gender in ['Male', 'Female', 'Other', 'NA']:
        user.gender = gender
        db.session.commit()

    return redirect(url_for('profile'))

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy_policy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@csrf.exempt
@app.route('/save-heart-rate', methods=['POST'])
def save_heart_rate():
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.get_json()

    record = HeartRateRecord(
        user_id=session['user_id'],
        bpm=data.get('bpm'),
        aqi=data.get('aqi'),
        stress_level=data.get('stress'),
        impact_category=data.get('impact')
    )

    db.session.add(record)
    db.session.commit()

    records = (
        HeartRateRecord.query
        .filter_by(user_id=session['user_id'])
        .order_by(HeartRateRecord.created_at.desc())
        .all()
    )

    if len(records) > 7:
        for old_record in records[7:]:
            db.session.delete(old_record)
        db.session.commit()

    return jsonify({'success': True})


@app.route('/api/heart-rate/last-7')
def get_last_7_heart_rates():
    if 'user_id' not in session:
        return jsonify([]), 401

    ist = pytz.timezone("Asia/Kolkata")

    records = (
        HeartRateRecord.query
        .filter_by(user_id=session['user_id'])
        .order_by(HeartRateRecord.created_at.desc())
        .limit(7)
        .all()
    )

    result = []
    for r in records:
        local_time = r.created_at.replace(tzinfo=pytz.utc).astimezone(ist)

        result.append({
            "bpm": r.bpm,
            "aqi": r.aqi,
            "stress": r.stress_level,
            "impact": r.impact_category,
            "time": local_time.strftime("%d %b %Y %I:%M %p")
        })

    return jsonify(result)

@app.route('/health')
def health():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('health.html')


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))

    user = db.session.get(User, session['user_id'])
    db.session.refresh(user)  

    return render_template('profile.html', user=user)


@app.route('/tracker')
def tracker():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return render_template('tracker.html')

def calculate_us_aqi(pm25):
    """Calculates US EPA AQI from PM2.5 concentration"""
    if pm25 is None: return None
    try:
        c = float(pm25)
        if c < 0: return 0
        if c <= 12.0: return round(((50 - 0) / (12.0 - 0)) * (c - 0) + 0)
        if c <= 35.4: return round(((100 - 51) / (35.4 - 12.1)) * (c - 12.1) + 51)
        if c <= 55.4: return round(((150 - 101) / (55.4 - 35.5)) * (c - 35.5) + 101)
        if c <= 150.4: return round(((200 - 151) / (150.4 - 55.5)) * (c - 55.5) + 151)
        if c <= 250.4: return round(((300 - 201) / (250.4 - 150.5)) * (c - 150.5) + 201)
        if c <= 350.4: return round(((400 - 301) / (350.4 - 250.5)) * (c - 250.5) + 301)
        if c <= 500.4: return round(((500 - 401) / (500.4 - 350.5)) * (c - 350.5) + 401)
        return 500
    except (ValueError, TypeError):
        return None

@csrf.exempt
@app.route("/api/aqi")
def get_aqi():
    city = request.args.get("city")
    if not city:
        return jsonify({"error": "City required"}), 400

    if not AQICN_API_TOKEN:
        return jsonify({"error": "AQICN token missing"}), 500

    #  GEOCODE CITY
    try:
        geo_resp = requests.get(
            "https://nominatim.openstreetmap.org/search",
            params={"q": city, "format": "json", "limit": 1},
            headers={"User-Agent": "HridyaCare/1.0"},
            timeout=10
        ).json()
    except Exception:
        return jsonify({"error": "Geocoding failed"}), 502

    if not geo_resp:
        return jsonify({"error": "City not found"}), 404

    lat = geo_resp[0]["lat"]
    lon = geo_resp[0]["lon"]

    # 2️ AQICN GEO FEED
    url = f"https://api.waqi.info/feed/geo:{lat};{lon}/"
    params = {"token": AQICN_API_TOKEN}

    try:
        resp = requests.get(url, params=params, timeout=10).json()
    except Exception:
        return jsonify({"error": "AQI API unreachable"}), 502

    if resp.get("status") != "ok":
        return jsonify({"error": "AQICN error", "details": resp}), 502

    data = resp["data"]

    raw_aqi = data["aqi"]
    pm25_val = data.get("iaqi", {}).get("pm25", {}).get("v")
    pm10_val = data.get("iaqi", {}).get("pm10", {}).get("v")

    calculated_aqi = calculate_us_aqi(pm25_val)

    final_aqi = calculated_aqi if calculated_aqi is not None else raw_aqi

    print(f"City: {city} | API Says: {raw_aqi} | PM2.5: {pm25_val} | Calculated: {final_aqi}")

    return jsonify({
        "city": city,
        "aqi": final_aqi,  
        "pm25": pm25_val,
        "pm10": pm10_val,
        "dominant": data.get("dominentpol"),
        "source": "AQICN / CPCB",
        "scale": "US EPA AQI"
    })

# pdf generation
@csrf.exempt
@app.route('/generate-pdf', methods=['POST'])
def generate_pdf():
    if 'user_id' not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    history = data.get("history", [])

    os.makedirs("static/reports", exist_ok=True)

    pdf_name = f"HridyaCare_Report_{uuid.uuid4().hex}.pdf"
    img_name = f"hr_graph_{uuid.uuid4().hex}.png"

    pdf_path = os.path.join("static", "reports", pdf_name)
    img_path = os.path.join("static", "reports", img_name)
    
    if history:
        bpm = [h.get("bpm", 0) for h in history]
        x = list(range(1, len(bpm) + 1))

        plt.figure(figsize=(6, 3))
        plt.plot(x, bpm, marker="o", linewidth=2)
        plt.fill_between(x, bpm, alpha=0.15)
        plt.title("Heart Rate Trend (Last 7 Readings)")
        plt.xlabel("Reading")
        plt.ylabel("BPM")
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(img_path, dpi=120)
        plt.close()


    c = canvas.Canvas(pdf_path, pagesize=A4)
    width, height = A4
    BOTTOM_MARGIN = 2 * cm

    LEFT_MARGIN = 2 * cm
    RIGHT_MARGIN = 2 * cm
    CONTENT_WIDTH = width - LEFT_MARGIN - RIGHT_MARGIN

    # ---------- HEADER ----------
    c.setFillColorRGB(0.96, 0.26, 0.39)
    c.rect(0, height - 70, width, 70, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 22)
    c.drawCentredString(width / 2, height - 45, "HridyaCare Health Report")

    y = height - 100
    c.setFillColor(colors.black)

    # ---------- USER INFO ----------
    c.setFont("Helvetica", 12)
    c.drawString(LEFT_MARGIN, y, f"Username: {data.get('name', 'User')}")
    c.drawRightString(width - RIGHT_MARGIN, y, f"Date: {data.get('timestamp')}")
    y -= 18

    c.drawString(LEFT_MARGIN, y, f"Age: {data.get('age')}")
    c.drawRightString(width - RIGHT_MARGIN, y, f"City: {data.get('city')}")
    y -= 30

    # ---------- HEART RATE CARD ----------
    c.setFillColorRGB(0.95, 0.96, 0.98)
    c.roundRect(LEFT_MARGIN, y - 80, CONTENT_WIDTH, 80, 12, fill=1)
    c.setFillColor(colors.black)

    c.setFont("Helvetica-Bold", 20)
    c.drawCentredString(width / 2, y - 35, f"{data.get('bpm')} BPM")

    c.setFont("Helvetica", 12)
    c.drawCentredString(width / 2, y - 60, f"Impact: {data.get('impactCategory')}")
    y -= 110

    # ---------- AQI DETAILS ----------
    c.setFillColorRGB(0.97, 0.97, 0.97)
    c.roundRect(LEFT_MARGIN, y - 70, CONTENT_WIDTH, 70, 10, fill=1)
    c.setFillColor(colors.black)

    c.setFont("Helvetica-Bold", 12)
    c.drawString(LEFT_MARGIN + 10, y - 28, f"AQI: {data.get('aqi', '--')} (US EPA)")

    c.setFont("Helvetica", 11)
    c.drawString(
        LEFT_MARGIN + 10,
        y - 48,
        f"PM2.5: {data.get('pm25', '--')} µg/m³"
    )
    c.drawRightString(
        width - RIGHT_MARGIN - 10,
        y - 48,
        f"PM10: {data.get('pm10', '--')} µg/m³"
    )

    y -= 90

    # ---------- GRAPH ----------
    if history and os.path.exists(img_path):
        c.drawImage(
            img_path,
            LEFT_MARGIN,
            y - 180,
            width=CONTENT_WIDTH,
            height=160,
            preserveAspectRatio=True
        )
        y -= 200

    # ---------- HEART RATE TABLE ----------
    if history:
        c.setFont("Helvetica-Bold", 14)
        c.drawString(LEFT_MARGIN, y, "Last 7 Heart Rate Readings")
        y -= 12

        hr_table_data = [["#", "BPM", "Time"]]
        for i, h in enumerate(history[::-1], 1):
            hr_table_data.append([str(i), str(h["bpm"]), h["time"]])

        hr_table = Table(
            hr_table_data,
            colWidths=[2 * cm, 3 * cm, CONTENT_WIDTH - 5 * cm]
        )

        hr_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("ALIGN", (0, 0), (-1, -1), "CENTER"),
            ("FONT", (0, 0), (-1, 0), "Helvetica-Bold"),
        ]))

        _, table_height = hr_table.wrap(CONTENT_WIDTH, height)
        hr_table.drawOn(c, LEFT_MARGIN, y - table_height)
        y -= table_height + 20

    # ---------- AQI REFERENCE TABLE ----------
    styles = getSampleStyleSheet()
    cell = styles["BodyText"]
    cell.fontSize = 9
    cell.leading = 11

    c.setFont("Helvetica-Bold", 14)

    if y < BOTTOM_MARGIN + 120:
        c.showPage()
        y = height - 60
        c.setFont("Helvetica-Bold", 14)

    c.drawString(LEFT_MARGIN, y, "AQI Reference (US EPA Scale)")
    y -= 14

    aqi_table_data = [
        [Paragraph("<b>AQI Range</b>", cell),
         Paragraph("<b>Category</b>", cell),
         Paragraph("<b>Health Meaning</b>", cell)],
        [Paragraph("0–50", cell), Paragraph("Good", cell),
         Paragraph("Air quality is satisfactory", cell)],
        [Paragraph("51–100", cell), Paragraph("Moderate", cell),
         Paragraph("Some pollutants may affect sensitive people", cell)],
        [Paragraph("101–150", cell), Paragraph("Unhealthy for Sensitive Groups", cell),
         Paragraph("People with lung/heart disease may be affected", cell)],
        [Paragraph("151–200", cell), Paragraph("Unhealthy", cell),
         Paragraph("Everyone may experience health effects", cell)],
        [Paragraph("201–300", cell), Paragraph("Very Unhealthy", cell),
         Paragraph("Health alert: increased risk", cell)],
        [Paragraph("301–500", cell), Paragraph("Hazardous", cell),
         Paragraph("Emergency conditions", cell)],
    ]

    aqi_table = Table(
        aqi_table_data,
        colWidths=[3 * cm, 5 * cm, CONTENT_WIDTH - 8 * cm]
    )

    aqi_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#fee2e2")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    _, aqi_height = aqi_table.wrap(CONTENT_WIDTH, height)
    
    if y - aqi_height < BOTTOM_MARGIN:
        c.showPage()
        y = height - 60

    aqi_table.drawOn(c, LEFT_MARGIN, y - aqi_height)
    y -= aqi_height + 20


    # ---------- DISCLAIMER ----------
    c.setFont("Helvetica-Oblique", 10)
    c.setFillColor(colors.grey)
    c.drawString(
        LEFT_MARGIN,
        y,
        "This report provides wellness insights and is not a medical diagnosis."
    )

    c.showPage()
    c.save()

    if os.path.exists(img_path):
        os.remove(img_path)

    return jsonify({
        "pdf_url": url_for(
            "static",
            filename=f"reports/{pdf_name}",
            _external=True
        )
    })


def coach_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("login"))

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT role FROM users WHERE id = %s", (session["user_id"],))
        role = cur.fetchone()
        cur.close()
        conn.close()

        if not role or role[0] != "coach":
            return redirect(url_for("index"))

        return f(*args, **kwargs)
    return wrapper

    
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":

        # ---------- BASIC FIELDS ----------
        username = request.form["username"].strip().lower()
        email = request.form["email"].strip().lower()
        password = (request.form.get("password") or "").strip()
        confirm_password = (request.form.get("confirm_password") or "").strip()
        print("PASSWORD:", repr(password))
        print("CONFIRM:", repr(confirm_password))
        role = request.form.get("role", "user")

        # ---------- VALIDATIONS ----------
        if username in RESERVED_USERNAMES:
            flash("This username is reserved.")
            return redirect(url_for("register"))

        if not password or password != confirm_password:
            flash("Password and Confirm Password must be identical.")
            return redirect(url_for("register"))

        conn = get_db_connection()
        cur = conn.cursor()

        # email check
        cur.execute("SELECT 1 FROM users WHERE email=%s", (email,))
        if cur.fetchone():
            cur.close()
            conn.close()
            flash("Email already registered.")
            return redirect(url_for("register"))

        # username check
        cur.execute("SELECT 1 FROM users WHERE username=%s", (username,))
        if cur.fetchone():
            cur.close()
            conn.close()
            flash("Username already taken.")
            return redirect(url_for("register"))

        password_hash = generate_password_hash(password)

        # ---------- ROLE LOGIC ----------
        verification_status = "pending" if role == "coach" else "approved"
        certificate_path = None

        # ---------- COACH CERTIFICATE ----------
        if role == "coach":
            file = request.files.get("certificate")

            if not file or file.filename == "":
                cur.close()
                conn.close()
                flash("Certificate is required for Health Coach.")
                return redirect(url_for("register"))

            if not allowed_file(file.filename):
                cur.close()
                conn.close()
                flash("Invalid certificate format.")
                return redirect(url_for("register"))

            filename = secure_filename(file.filename)
            certificate_path = f"{uuid.uuid4().hex}_{filename}"
            save_path = os.path.join(app.config["UPLOAD_FOLDER"], certificate_path)
            file.save(save_path)

        # ---------- INSERT USER ----------
        cur.execute("""
            INSERT INTO users
            (username, email, password_hash, role, verification_status, certificate_path)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (
            username,
            email,
            password_hash,
            role,
            verification_status,
            certificate_path
        ))

        conn.commit()
        cur.close()
        conn.close()

        flash("Account created successfully. Please sign in.")
        return redirect(url_for("login"))

    # ---------- GET ----------
    return render_template("register.html")


@app.route("/coach/entry")
def coach_entry():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT role, verification_status FROM users WHERE id = %s",
        (session["user_id"],)
    )
    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user or user["role"] != "coach":
        return redirect(url_for("index"))

    if user["verification_status"] == "approved":
        return redirect(url_for("coach_dashboard"))

    return redirect(url_for("coach_pending"))
 
@app.route("/")
def index():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template("index.html")

@app.route("/admin/coaches")
def admin_coaches():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # verify admin
    cur.execute(
        "SELECT role FROM users WHERE id = %s",
        (session["user_id"],)
    )
    admin = cur.fetchone()

    if not admin or admin["role"] != "admin":
        cur.close()
        conn.close()
        return redirect(url_for("index"))

    # ONLY PENDING COACHES
    cur.execute("""
        SELECT
            id,
            username,
            email,
            certificate_path
        FROM users
        WHERE role = 'coach'
          AND verification_status = 'pending'
        ORDER BY id DESC
    """)
    coaches = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "admin_coaches.html",
        coaches=coaches
    )



@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor(cursor_factory=RealDictCursor)

        cur.execute("SELECT * FROM users WHERE email = %s", (email,))
        user = cur.fetchone()

        cur.close()
        conn.close()

        if not user or not check_password_hash(user["password_hash"], password):
            session.clear()
            flash("Invalid email or password")
            return redirect(url_for("login"))


        session["user_id"] = user["id"]
        session["username"] = user["username"]

        print("LOGIN USER:", session["username"])  # DEBUG

        if user["role"] == "admin":
            return redirect(url_for("admin_coaches"))

        elif user["role"] == "coach":
            return redirect(url_for("coach_entry"))

        else:
            return redirect(url_for("index"))
    return render_template("login.html")

@csrf.exempt
@app.route("/admin/coach/approve/<int:coach_id>")
def approve_coach(coach_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    # verify admin
    cur.execute(
        "SELECT role FROM users WHERE id = %s",
        (session["user_id"],)
    )
    admin = cur.fetchone()

    if not admin or admin["role"] != "admin":
        cur.close()
        conn.close()
        return redirect(url_for("index"))

    cur.execute(
        "UPDATE users SET verification_status = 'approved' WHERE id = %s",
        (coach_id,)
    )

    conn.commit()
    cur.close()
    conn.close()

    flash("Coach approved successfully.", "success")
    return redirect(url_for("admin_coaches"))

@csrf.exempt
@app.route("/admin/coach/reject/<int:coach_id>")
def reject_coach(coach_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT role FROM users WHERE id = %s",
        (session["user_id"],)
    )
    admin = cur.fetchone()

    if not admin or admin["role"] != "admin":
        cur.close()
        conn.close()
        return redirect(url_for("index"))

    cur.execute(
        "UPDATE users SET verification_status = 'rejected' WHERE id = %s",
        (coach_id,)
    )

    conn.commit()
    cur.close()
    conn.close()

    flash("Coach rejected.", "info")
    return redirect(url_for("admin_coaches"))


@app.route("/uploads/certificates/<path:filename>")
def view_certificate(filename):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT role FROM users WHERE id = %s",
        (session["user_id"],)
    )
    user = cur.fetchone()

    cur.close()
    conn.close()

    if not user or user["role"] != "admin":
        return redirect(url_for("index"))

    filename = os.path.basename(filename)

    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)

    if not os.path.exists(file_path):
        return "Certificate file not found", 404

    return send_file(file_path)

@app.route("/api/coach/patient/<int:user_id>")
def get_patient_details(user_id):
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # verify coach
    cur.execute(
        "SELECT role FROM users WHERE id = %s",
        (session["user_id"],)
    )
    coach = cur.fetchone()

    if not coach or coach["role"] != "coach":
        cur.close()
        conn.close()
        return jsonify({"error": "Forbidden"}), 403

    # latest metrics
    cur.execute("""
        SELECT avg_bpm, stress_level, mls
        FROM health_metrics
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (user_id,))
    metrics = cur.fetchone()

    # coach notes
    cur.execute("""
        SELECT note, created_at
        FROM coach_notes
        WHERE user_id = %s
        ORDER BY created_at DESC
    """, (user_id,))
    notes = cur.fetchall()

    cur.close()
    conn.close()

    return jsonify({
        "metrics": metrics,
        "notes": [
            {
                "note": n["note"],
                "date": n["created_at"].strftime("%d %b %Y")
            } for n in notes
        ]
    })


@csrf.exempt
@app.route("/api/coach/add-note", methods=["POST"])
def add_coach_note():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.json
    patient_id = data.get("patient_id")
    note = data.get("note")

    if not patient_id or not note:
        return jsonify({"error": "Invalid data"}), 400

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute(
        "SELECT role FROM users WHERE id = %s",
        (session["user_id"],)
    )
    coach = cur.fetchone()

    if not coach or coach["role"] != "coach":
        cur.close()
        conn.close()
        return jsonify({"error": "Forbidden"}), 403

    # save note
    cur.execute("""
        INSERT INTO coach_notes (coach_id, user_id, note)
        VALUES (%s, %s, %s)
    """, (
        session["user_id"],
        patient_id,
        note
    ))

    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"status": "saved"})

@app.route("/api/coach/profile")
def coach_profile():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT
            id,
            username,
            email,
            role,
            verification_status
        FROM users
        WHERE id = %s
          AND role = 'coach'
    """, (session["user_id"],))

    coach = cur.fetchone()
    cur.close()
    conn.close()

    if not coach:
        return jsonify({"error": "Not a coach"}), 403

    return jsonify({
        "id": coach["id"],
        "name": coach["username"],
        "email": coach["email"],
        "status": coach["verification_status"]
    })


@app.route("/api/telehealth/data")
def telehealth_data():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT avg_bpm, stress_level
        FROM health_metrics
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (session["user_id"],))
    metrics = cur.fetchone()

    cur.execute("""
        SELECT note, created_at
        FROM coach_notes
        WHERE user_id = %s
        ORDER BY created_at DESC
        LIMIT 1
    """, (session["user_id"],))
    note = cur.fetchone()

    cur.close()
    conn.close()

    return jsonify({
        "avg_bpm": metrics["avg_bpm"] if metrics else "--",
        "stress": metrics["stress_level"] if metrics else "--",
        "coach_note": note["note"] if note else None
    })

@csrf.exempt
@app.route('/logout', methods=["POST"])
def logout():
    session.clear()   
    flash('Logged out successfully.', 'info')
    return redirect(url_for('login'))


def diet_recommendation(bpm):
    if bpm < 60:
        return "Energy-support diet (complex carbs, hydration)"
    elif 60 <= bpm <= 90:
        return "Balanced heart-healthy diet"
    else:
        return "Stress-reduction & low-salt diet"
    
@app.route("/api/diet")
def api_diet():
    bpm = int(request.args.get("bpm", 72)) 
    return {
        "bpm": bpm,
        "recommendation": diet_recommendation(bpm)
    }



@app.route("/article/<slug>")
def article_page(slug):
    article = ARTICLES.get(slug)
    if not article:
        return "Article not found", 404

    return render_template("article.html", article=article)


ARTICLES = {
    "resting-heart-rate": {
        "title": "Resting Heart Rate Explained",
        "category": "Heart Health",
        "read_time": "4 min",
        "content": """
Your resting heart rate (RHR) is the number of times your heart beats per minute while at complete rest.

A lower resting heart rate usually indicates better cardiovascular fitness and heart efficiency.

• Average adult RHR: 60–100 BPM  
• Athletes: 40–60 BPM  
• High RHR may indicate stress, dehydration, or illness

Improving sleep, reducing stress, and regular exercise can help lower resting heart rate.
"""
    },
    "heart-healthy-diet": {
        "title": "Best Foods for Heart Health",
        "category": "Diet",
        "read_time": "5 min",
        "content": """
A heart-healthy diet focuses on whole foods, healthy fats, and low sodium intake.

Recommended foods:
• Nuts and seeds
• Fruits & vegetables
• Whole grains
• Omega-3 rich foods (fish, flaxseed)

Avoid excessive sugar, fried foods, and processed meats.
"""
    }
}

ARTICLES["resting-heart-rate"]["recommended_by"] = "Dr. Cardiology"
ARTICLES["heart-healthy-diet"]["recommended_by"] = "Health Coach"

def ai_pick_article(bpm):
    if bpm > 90:
        return "resting-heart-rate"
    return "heart-healthy-diet"

@app.route("/api/ai-read")
def ai_read():
    bpm = 88  # later from DB
    slug = ai_pick_article(bpm)
    return {"slug": slug, "article": ARTICLES[slug]}

@csrf.exempt
@app.route("/api/physical-health", methods=["POST"])
def api_physical_health():
    if "user_id" not in session:
        return jsonify({"error": "Unauthorized"}), 401

    data = request.get_json()

    try:
        age = int(data.get("age"))
        weight = float(data.get("weight"))
        height = float(data.get("height"))

        if (
            age < 5 or age > 100 or
            weight < 20 or weight > 200 or
            height < 100 or height > 220
        ):
            return jsonify({"error": "Invalid input values"}), 400

        wasi = calculate_wasi(age, weight, height)
        mls = calculate_mls(age, weight, height)

        return jsonify({
            "wasi": wasi,
            "mls": mls
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)

