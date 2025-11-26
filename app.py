from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR / "users.db"

app = Flask(__name__)
app.secret_key = "key" # TODO: Get secret key

# Connect to database
def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


# Close databse connection on exit
@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


@app.route("/")
def index():
    # Redirect to dashboard if user logged in...
    if session.get("user_id"):
        return redirect(url_for("dashboard"))
    # Else redirect to login
    return redirect(url_for("login"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET": # Serve form
            return render_template("register.html")
    else: # On form submit
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        supercell_id = request.form.get("supercell_id", "")
        # Validate credentials
        if not username or not email or not password:
            flash("Please fill in all required fields.", "error")
            return render_template("register.html")
        if password != password_confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")
        # TODO: Check if supercell_id is valid
        # Add account to database
        db = get_db()
        try:
            password_hash = generate_password_hash(password)
            db.execute(
                "INSERT INTO users (username, email, password_hash, supercell_id) VALUES (?, ?, ?, ?)",
                (username, email, password_hash, supercell_id),
            )
            db.commit()
            flash("Account created — please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError as e:
            if "username" in str(e).lower():
                flash("Username already taken.", "error")
            elif "email" in str(e).lower():
                flash("Email already registered.", "error")
            else:
                flash("An error occurred. Try again.", "error")
            return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET": # Serve form
        return render_template("login.html")
    else: # On form submit
        identifier = request.form.get("identifier", "").strip()  # Username or email
        password = request.form.get("password", "")
        # Validate credentials
        if not identifier or not password:
            flash("Enter username/email and password.", "error")
            return render_template("login.html")
        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username = ? COLLATE NOCASE OR email = ? COLLATE NOCASE",
            (identifier, identifier),
        ).fetchone()
        if user and check_password_hash(user["password_hash"], password): # Login success
            session.clear()
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash("Logged in successfully.", "success")
            return redirect(url_for("dashboard"))
        else: # Login failed
            flash("Invalid credentials.", "error")
            return render_template("login.html")


@app.route("/dashboard")
def dashboard():
    if not session.get("user_id"): # Cannot see dashboard unless logged in
        flash("Please log in to see the dashboard.", "error")
        return redirect(url_for("login"))
    return render_template("dashboard.html", username=session.get("username"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    if not DATABASE.exists():
        print("Database not found. Initialize with: python init_db.py")
    app.run(host='0.0.0.0', port=5000, debug=True)