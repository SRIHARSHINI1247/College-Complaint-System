import os
from datetime import datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "change-me")
# Local: SQLite. On AWS: mysql+pymysql://user:pass@<rds-endpoint>/complaintdb
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL", "sqlite:///complaints.db")
db = SQLAlchemy(app)

STATUSES = ["Submitted", "Assigned", "In Progress", "Resolved"]
CATEGORIES = ["Lab Equipment", "Classroom", "Wi-Fi", "Projector", "Other"]


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(10), default="student")  # student / admin


class Complaint(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    category = db.Column(db.String(30), nullable=False)
    location = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default="Submitted")
    assigned_to = db.Column(db.String(100))
    remarks = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user = db.relationship("User")


def login_required(role=None):
    def deco(f):
        @wraps(f)
        def wrapper(*a, **kw):
            if "uid" not in session:
                return redirect(url_for("login"))
            if role and session.get("role") != role:
                flash("Not authorised.")
                return redirect(url_for("dashboard"))
            return f(*a, **kw)
        return wrapper
    return deco


@app.route("/")
def index():
    return redirect(url_for("dashboard"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"].strip().lower()
        if User.query.filter_by(email=email).first():
            flash("Email already registered.")
        else:
            db.session.add(User(name=request.form["name"], email=email, role="student",
                                password_hash=generate_password_hash(request.form["password"])))
            db.session.commit()
            flash("Registered successfully. Please log in.")
            return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        u = User.query.filter_by(email=request.form["email"].strip().lower()).first()
        if u and check_password_hash(u.password_hash, request.form["password"]):
            session.update(uid=u.id, name=u.name, role=u.role)
            return redirect(url_for("dashboard"))
        flash("Invalid email or password.")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/dashboard")
@login_required()
def dashboard():
    if session["role"] == "admin":
        return redirect(url_for("admin"))
    items = Complaint.query.filter_by(user_id=session["uid"]).order_by(Complaint.id.desc()).all()
    return render_template("dashboard.html", items=items)


@app.route("/complaint/new", methods=["GET", "POST"])
@login_required("student")
def new_complaint():
    if request.method == "POST":
        db.session.add(Complaint(user_id=session["uid"], category=request.form["category"],
                                 location=request.form["location"],
                                 description=request.form["description"]))
        db.session.commit()
        flash("Complaint submitted.")
        return redirect(url_for("dashboard"))
    return render_template("new.html", categories=CATEGORIES)


@app.route("/admin")
@login_required("admin")
def admin():
    status = request.args.get("status")
    q = Complaint.query
    if status in STATUSES:
        q = q.filter_by(status=status)
    counts = {s: Complaint.query.filter_by(status=s).count() for s in STATUSES}
    return render_template("admin.html", items=q.order_by(Complaint.id.desc()).all(),
                           statuses=STATUSES, counts=counts, current=status)


@app.route("/admin/update/<int:cid>", methods=["POST"])
@login_required("admin")
def update(cid):
    c = db.get_or_404(Complaint, cid)
    c.status = request.form["status"]
    c.assigned_to = request.form["assigned_to"]
    c.remarks = request.form["remarks"]
    db.session.commit()
    flash(f"Complaint #{cid} updated.")
    return redirect(url_for("admin"))


@app.route("/health")
def health():
    return "ok"


def init_db():
    with app.app_context():
        db.create_all()
        # Built-in admin account (students register themselves)
        admin_email = os.getenv("ADMIN_EMAIL", "admin@college.edu")
        if not User.query.filter_by(email=admin_email).first():
            db.session.add(User(
                name="Admin", email=admin_email, role="admin",
                password_hash=generate_password_hash(os.getenv("ADMIN_PASSWORD", "admin123"))))
            db.session.commit()


init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)