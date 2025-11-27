from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path
import requests

BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR / "users.db"

app = Flask(__name__)
app.secret_key = "key" # TODO: Get secret key

API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6IjBkMWI4YmYxLWYyNzAtNGZmNy1iOTlhLWFmZjFhNTRjMDg5OCIsImlhdCI6MTc2NDI1NzQyMSwic3ViIjoiZGV2ZWxvcGVyL2Y3YjA5OWM3LTViZmItNDJhOC1mYzUzLTUzNWRjODI4NTJiMCIsInNjb3BlcyI6WyJyb3lhbGUiXSwibGltaXRzIjpbeyJ0aWVyIjoiZGV2ZWxvcGVyL3NpbHZlciIsInR5cGUiOiJ0aHJvdHRsaW5nIn0seyJjaWRycyI6WyI3My4xMjYuMTQyLjExIl0sInR5cGUiOiJjbGllbnQifV19.zNv5pei5V-J_q7QzrLVCRhiC4GACsWIktZ8V43ruv9RUvJkTyi7fCAmsHaqLM75cC3bVXOtRuRerc5N9HGUIoA"

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
        player_tag = request.form.get("player_tag", "").strip().upper
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
        # TODO: Check if player_tag is valid
        # Add account to database
        db = get_db()
        try:
            password_hash = generate_password_hash(password)
            db.execute(
                "INSERT INTO users (username, email, password_hash, player_tag) VALUES (?, ?, ?, ?)",
                (username, email, password_hash, player_tag),
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
            session["player_tag"] = user["player_tag"]
            # TODO: just store data in session?
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
    tag = session.get('player_tag')
    url = f"https://api.clashroyale.com/v1/players/%23{tag}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return render_template("dashboard.html", data=data, player_tag=tag, error=None) # TODO: just include player_tag in data?
    except requests.RequestException as e:
        return render_template("dashboard.html", data=None, player_tag=tag, error=str(e))    


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("login"))


if __name__ == "__main__":
    if not DATABASE.exists():
        print("Database not found. Initialize with: python init_db.py")
    app.run(debug=True)
