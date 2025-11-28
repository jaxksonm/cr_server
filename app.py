from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path
import requests
from datetime import datetime
from math import ceil, log2

import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
DATABASE = BASE_DIR / "users.db"

app = Flask(__name__)
app.secret_key = "key" # TODO: Get secret key


dotenv_path = Path(".env")
load_dotenv(dotenv_path=dotenv_path)

# Load the API_KEY from .env
API_KEY = os.getenv('API_KEY')

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
    return redirect(url_for("home"))


@app.route("/home")
def home():
    if not session.get("user_id"): # User not logged in
        return render_template("home.html", data=None)
    else: # User logged in
        player_tag = session.get('player_tag')
        url = f"https://api.clashroyale.com/v1/players/%23{player_tag}"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return render_template("home.html", data=data)
        except requests.RequestException as e:
            return render_template("home.html", data=None)    


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET": # Serve form
            return render_template("register.html")
    else: # On form submit
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        player_tag = request.form.get("player_tag", "").strip().upper()
        if (player_tag == "UCVLLVL" or player_tag == "JVGPUV20"): # Only Ronan and Jackson's accoutns are admins
            is_admin = 1
        else:
            is_admin = 0    
        # Validate credentials
        if not username or not email or not password or not player_tag:
            flash("Please fill in all required fields.", "error")
            return render_template("register.html")
        if password != password_confirm:
            flash("Passwords do not match.", "error")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template("register.html")
        url = f"https://api.clashroyale.com/v1/players/%23{player_tag}"
        headers = {"Authorization": f"Bearer {API_KEY}"}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            flash("Enter valid player tag.", "error")
            return render_template("register.html")  
        # Add account to database
        db = get_db()
        try:
            password_hash = generate_password_hash(password)
            db.execute(
                "INSERT INTO users (username, email, password_hash, player_tag, is_admin) VALUES (?, ?, ?, ?, ?)",
                (username, email, password_hash, player_tag, is_admin),
            )
            db.commit()
            flash("Account created — please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError as e:
            if "username" in str(e).lower():
                flash("Username already taken.", "error")
            elif "email" in str(e).lower():
                flash("Email already registered.", "error")
            elif "player_tag" in str(e).lower():
                flash("Player tag already registered.", "error")
            else:
                flash("An error occurred. Try again.", "error")
            return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET": # Serve form
        return render_template("login.html")
    else: # On form submit
        identifier = request.form.get("identifier", "").strip() # Username or email
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
            session["points"] = user["points"]
            session["is_admin"] = user["is_admin"]
            flash("Logged in successfully.", "success")
            return redirect(url_for("home"))
        else: # Login failed
            flash("Invalid credentials.", "error")
            return render_template("login.html")


@app.route("/profile")
def profile():
    if not session.get("user_id"): # Cannot see profile unless logged in
        flash("Please log in to see profile.", "error")
        return redirect(url_for("login"))
    tag = session.get('player_tag')
    points = session.get('points')
    url = f"https://api.clashroyale.com/v1/players/%23{tag}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return render_template("profile.html", data=data, player_tag=tag, points=points) # TODO: is player tag included in data?
    except requests.RequestException as e:
        return render_template("profile.html", data=None, player_tag=tag, points=points)    


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("login"))


def create_bracket(participants):
    # sort by seed (0 means unspecified -> lowest priority)
    participants_sorted = sorted(participants, key=lambda p: (p[2] if p[2] is not None else 9999))
    ids = [p[0] for p in participants_sorted]
    n = len(ids)
    if n == 0:
        return []

    # Next power of two
    next_pow2 = 1 << (ceil(log2(n)))
    byes = next_pow2 - n

    # Simple seeding pairing: pair highest with lowest, etc.
    # Create initial bracket slots of length next_pow2 with byes as None
    slots = ids[:] + [None] * byes

    # initial round pairings
    pairs = []
    while len(slots) > 1:
        new_pairs = []
        for i in range(0, len(slots), 2):
            new_pairs.append((slots[i], slots[i+1] if i+1 < len(slots) else None))
        pairs.append(new_pairs)
        # winners placeholders for next round: use None placeholders
        slots = [None] * (len(new_pairs))
    return pairs


@app.route("/tournaments")
def tournaments_list():
    db = get_db()
    rows = db.execute("SELECT id, name, date, created_at FROM tournaments ORDER BY date ASC").fetchall()
    return render_template("tournaments/list.html", tournaments=rows, is_admin = session.get("is_admin"))


@app.route("/tournaments/create", methods=["GET", "POST"])
def tournaments_create():
    if request.method == "GET":
        return render_template("tournaments/create.html")
    else:
        name = request.form.get("name", "").strip()
        date = request.form.get("date", "")
        description = request.form.get("description", "")
        if not name or not date:
            flash("Enter name and date.", "error")
            return render_template("tournaments/create.html")
        if not description:
            description = "No description."
        # Attempt to format date
        try:
            d = datetime.fromisoformat(date)
            formatted_date = d.strftime("%B %d, %Y at %I:%M %p")  
        except:
            formatted_date = date
        db = get_db()
        db.execute("INSERT INTO tournaments (name, description, date) VALUES (?, ?, ?)", (name, description, formatted_date))
        db.commit()
        flash("Tournament created.", "success")
        return redirect(url_for("tournaments_list"))


@app.route("/tournaments/<int:tid>", methods=["GET", "POST"])
def tournament_view(tid):
    db = get_db()
    tour = db.execute("SELECT id, name, description, date, created_at FROM tournaments WHERE id = ?", (tid,)).fetchone()
    if not tour:
        flash("Tournament not found.", "error")
        return redirect(url_for("tournaments_list"))
    # Add participant
    if request.method == "POST" and request.form.get("action") == "add_participant":
        pname = request.form.get("participant_name", "").strip()
        pseed = request.form.get("seed", "").strip()
        seed_val = int(pseed) if pseed.isdigit() else None
        if pname:
            db.execute("INSERT INTO participants (tournament_id, name, seed) VALUES (?, ?, ?)", (tid, pname, seed_val))
            db.commit()
            flash("Participant added.", "success")
            return redirect(url_for("tournament_view", tid=tid))
        else:
            flash("Participant name required.", "error")
            return redirect(url_for("tournament_view", tid=tid))
    # Generate bracket
    parts = db.execute("SELECT id, name, seed FROM participants WHERE tournament_id = ? ORDER BY seed ASC, id ASC", (tid,)).fetchall()
    participants = [(r["id"], r["name"], r["seed"]) for r in parts]
    # If user requested to auto-generate initial matches:
    if request.args.get("generate") == "1":
        # delete existing matches for this tournament to regenerate
        db.execute("DELETE FROM matches WHERE tournament_id = ?", (tid,))
        # create initial pairings
        rounds = create_bracket(participants)
        # rounds is list of rounds; we will only insert round 1 pairings
        if rounds:
            round1 = rounds[0]
            for p1, p2 in round1:
                db.execute(
                    "INSERT INTO matches (tournament_id, round, player1_id, player2_id) VALUES (?, ?, ?, ?)",
                    (tid, 1, p1, p2)
                )
            db.commit()
            flash("Bracket generated (round 1 created).", "success")
            return redirect(url_for("tournament_view", tid=tid))
    # Load matches grouped by round
    match_rows = db.execute("SELECT * FROM matches WHERE tournament_id = ? ORDER BY round, id", (tid,)).fetchall()
    rounds = {}
    for m in match_rows:
        rounds.setdefault(m["round"], []).append(m)
    return render_template("tournaments/view.html", tournament=tour, participants=participants, rounds=rounds)


if __name__ == "__main__":
    if not DATABASE.exists():
        print("Database not found. Initialize with: python init_db.py")
    app.run(debug=True)
