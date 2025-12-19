from flask import Flask, render_template, request, redirect, url_for, session, flash, g
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from pathlib import Path
import requests
from datetime import datetime
from math import ceil, log2
# imports for the api key routing 
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")

DATABASE = BASE_DIR / "users.db"

app = Flask(__name__)
app.secret_key = "key" # TODO: Get secret key

def get_api_key():
    key = os.getenv("API_KEY")
    if not key:
        raise RuntimeError("not a valid api key for variable")
    return key


def get_available_pfp(): # Get all available pfps for dropdown menu in profile_edit
    pfp_dir = BASE_DIR / "static" / "pfp"
    if not pfp_dir.exists():
        return []
    pfp_files = []
    for file in sorted(pfp_dir.iterdir()):
        if file.suffix in ['.webp', '.png']:
            pfp_files.append(file.stem)
    return pfp_files


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
    db = get_db()
    recent_announcements = db.execute(
        "SELECT id, pfp, rarity, username, cr_username, announcement, created_at FROM announcements ORDER BY created_at DESC LIMIT 3"
    ).fetchall()
    if not session.get("user_id"): # User not logged in
        return render_template("home.html", data=None, recent_announcements=recent_announcements)
    else: # User logged in
        player_tag = session.get('player_tag')
        url = f"https://api.clashroyale.com/v1/players/%23{player_tag}"
        headers = {"Authorization": f"Bearer {get_api_key()}"}

        try: # TODO: Remove unnecesary API calls, they really slow it down!!!!
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
            return render_template("home.html", data=data, recent_announcements=recent_announcements)
        except requests.RequestException as e:
            return render_template("home.html", data=None, recent_announcements=recent_announcements)    


@app.route("/announcements", methods=["GET", "POST"])
def announcements():
    db = get_db()
    if (request.method == "POST"):
        username = session.get("username")
        pfp = session.get("pfp")
        rarity = session.get("rarity")
        cr_username = session.get("cr_username")
        announcement = request.form.get("announcement", "")
        db.execute(
                "INSERT INTO announcements (username, pfp, rarity, cr_username, announcement) VALUES (?, ?, ?, ?, ?)",
                (username, pfp, rarity, cr_username, announcement),
            )
        db.commit()
        flash("Announcement posted.", "success")
    announcements = db.execute(
        "SELECT id, pfp, rarity, username, cr_username, announcement, created_at FROM announcements ORDER BY created_at DESC"
    ).fetchall()
    return render_template("announcements.html", announcements=announcements)


@app.route("/announcements/delete/<int:aid>", methods=["POST"])
def announcement_delete(aid):
    if not session.get("is_admin"):
        flash("Only admins can delete announcements.", "error")
        return redirect(url_for("announcements"))
    db = get_db()
    try:
        db.execute("DELETE FROM announcements WHERE id = ?", (aid,))
        db.commit()
        flash("Announcement deleted.", "success")
        return redirect(url_for("announcements"))
    except Exception as e:
        db.rollback()
        app.logger.exception("Error deleting announcement")
        flash("Could not delete announcement.", "error")
        return redirect(url_for("announcements"))


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET": # Serve form
            return render_template("register.html")
    else: # On form submit
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")
        player_tag = request.form.get("player_tag", "").strip().upper().lstrip("#")
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
        if len(password) < 8:
            flash("Password must be at least 8 characters.", "error")
            return render_template("register.html")
        url = f"https://api.clashroyale.com/v1/players/%23{player_tag}"
        headers = {"Authorization": f"Bearer {get_api_key()}"}

        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            flash("Enter valid player tag.", "error")
            return render_template("register.html")  
        cr_username = data["name"]
        # Add account to database
        db = get_db()
        try:
            password_hash = generate_password_hash(password)
            db.execute(
                "INSERT INTO users (username, email, password_hash, cr_username, player_tag, is_admin) VALUES (?, ?, ?, ?, ?, ?)",
                (username, email, password_hash, cr_username, player_tag, is_admin),
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
            session["pfp"] = user["pfp"]
            session["rarity"] = user["rarity"]
            session["username"] = user["username"]
            session["cr_username"] = user["cr_username"]
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
    url = f"https://api.clashroyale.com/v1/players/%23{session.get('player_tag')}"
    headers = {"Authorization": f"Bearer {get_api_key()}"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return render_template("profile.html", data=data)
    except requests.RequestException as e:
        flash("Unable to access Clash Royale API using player tag", "error")
        return render_template("profile.html", data=None)


@app.route("/profile/delete", methods=["POST"])
def profile_delete():
    if not session.get("user_id"):
        flash("Please log in to delete profile.", "error")
        return redirect(url_for("login"))
    uid = session["user_id"]
    db = get_db()
    try:
        # 1. Find participant ids linked to this user (supports multiple in case we want to allow joining multiple tournaments)
        p_rows = db.execute("SELECT id FROM participants WHERE user_id = ?", (uid,)).fetchall()
        pids = [r["id"] for r in p_rows]
        # 2. Delete matches that reference those participant ids
        if pids:
            for pid in pids:
                db.execute("DELETE FROM matches WHERE player1_id = ? OR player2_id = ?", (pid, pid))
        # 3. Delete participant rows for this user
        db.execute("DELETE FROM participants WHERE user_id = ?", (uid,))
        # 4. Delete the user row
        db.execute("DELETE FROM users WHERE id = ?", (uid,))
        db.commit()
    except Exception as e:
        db.rollback()
        app.logger.exception("Error deleting profile for user %s: %s", uid, e)
        flash("Could not delete profile. Contact an admin.", "error")
        return redirect(url_for("profile"))
    # 5. Clear session and redirect to home
    session.clear()
    flash("Your profile was deleted.", "success")
    return redirect(url_for("home"))

@app.route("/chat")
def chat():
    # if not session.get("user_id"):
    #     flash("Please log in to use chat.", "error")
    #     return redirect(url_for("login"))

    db = get_db()
    messages = db.execute("""
        SELECT chat_messages.message,
               chat_messages.created_at,
               users.username,
               users.pfp,
               users.rarity
        FROM chat_messages
        JOIN users ON chat_messages.user_id = users.id
        ORDER BY chat_messages.created_at ASC
        LIMIT 50
    """).fetchall()

    return render_template("chat.html", messages=messages)


@app.route("/chat/send", methods=["POST"])
def chat_send():
    if not session.get("user_id"):
        return {"error": "Not logged in"}, 401
    ####temp admin only chat access while under construction###########
    if not session.get("is_admin"):
        return {"error": "Admins only"}, 403
    ####################################################################
    data = request.get_json()
    message = data.get("message", "").strip()

    if not message:
        return {"error": "Empty message"}, 400

    db = get_db()
    db.execute(
        "INSERT INTO chat_messages (user_id, message) VALUES (?, ?)",
        (session["user_id"], message),
    )
    db.commit()

    return {
        "username": session["username"],
        "message": message
    }

@app.route("/profile/edit", methods=["GET", "POST"])
def profile_edit():
    if not session.get("user_id"):
        flash("Please log in to edit your profile.", "error")
        return redirect(url_for("login"))
    db = get_db()
    uid = session["user_id"]
    # Fetch user
    user = db.execute(
        "SELECT id, pfp, username, email, player_tag FROM users WHERE id = ?",
        (uid,)
    ).fetchone()
    if not user:
        flash("User not found.", "error")
        return redirect(url_for("logout"))
    current_pfp = user["pfp"]    
    current_username = user["username"]
    current_email = user["email"]
    current_player_tag = user["player_tag"]
    available_pfp = get_available_pfp()
    if request.method == "GET":
        return render_template(
            "profile_edit.html",
            pfp=current_pfp,
            username=current_username,
            email=current_email,
            player_tag=current_player_tag,
            available_pfp=available_pfp,
        )
    # Get new username/email.pass
    form_username = request.form.get("username", "").strip()
    form_pfp = request.form.get("pfp", "").strip()
    form_email = request.form.get("email", "").strip().lower()
    form_current_password = request.form.get("current_password", "")
    form_new_password = request.form.get("new_password", "")
    form_new_password_confirm = request.form.get("new_password_confirm", "")
    # Validate
    change_password = False
    new_hash = None
    if form_new_password or form_new_password_confirm:
        if not form_current_password:
            flash("Enter your current password to change your password.", "error")
            return render_template(
                "profile_edit.html",
                username=form_username,
                email=form_email,
                player_tag=current_player_tag,
            )
        if form_new_password != form_new_password_confirm:
            flash("New passwords do not match.", "error")
            return render_template(
                "profile_edit.html",
                username=form_username,
                email=form_email,
                player_tag=current_player_tag,
            )
        row = db.execute(
            "SELECT password_hash FROM users WHERE id = ?",
            (uid,)
        ).fetchone()
        if not check_password_hash(row["password_hash"], form_current_password):
            flash("Current password is incorrect.", "error")
            return render_template(
                "profile_edit.html",
                username=form_username,
                email=form_email,
                player_tag=current_player_tag,
            )
        new_hash = generate_password_hash(form_new_password)
        change_password = True
    # Update database
    try:
        if form_username != "":
            db.execute(
                "UPDATE users SET username = ? WHERE id = ?",
                (form_username, uid),
            )
            session["username"] = form_username
        if form_pfp != "":
            db.execute(
                "UPDATE users SET pfp = ? WHERE id = ?",
                (form_pfp, uid),
            )
            session["pfp"] = form_pfp
        if form_email != "":
            db.execute(
                "UPDATE users SET email = ? WHERE id = ?",
                (form_email, uid),
            )
        if change_password:
            db.execute(
                "UPDATE users SET password_hash = ? WHERE id = ?",
                (new_hash, uid),
            )
        db.commit()
    except sqlite3.IntegrityError as e:
        msg = str(e).lower()
        if "username" in msg:
            flash("Username already taken.", "error")
        elif "email" in msg:
            flash("Email already registered.", "error")
        else:
            flash("An error occurred while updating your profile.", "error")
        return render_template(
            "edit_profile.html",
            username=form_username,
            email=form_email,
            player_tag=current_player_tag,
        )
    # Update session
    flash("Profile updated.", "success")
    return redirect(url_for("profile"))


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out.", "success")
    return redirect(url_for("login"))


def create_bracket(participants):
    # Sort by seed (0 means unspecified -> lowest priority)
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
    # Initial round pairings
    pairs = []
    while len(slots) > 1:
        new_pairs = []
        for i in range(0, len(slots), 2):
            new_pairs.append((slots[i], slots[i+1] if i+1 < len(slots) else None))
        pairs.append(new_pairs)
        # Winners placeholders for next round: use None placeholders
        slots = [None] * (len(new_pairs))
    return pairs


@app.route("/tournaments")
def tournaments_list():
    db = get_db()
    rows = db.execute("SELECT id, name, description, date, location FROM tournaments ORDER BY date ASC").fetchall()
    return render_template("tournaments/list.html", tournaments=rows)


@app.route("/tournaments/create", methods=["GET", "POST"])
def tournaments_create():
    if request.method == "GET": # Serve form
        return render_template("tournaments/create.html")
    else: # On form submit
        name = request.form.get("name", "").strip()
        description = request.form.get("description", "")
        date = request.form.get("date", "")
        location = request.form.get("location", "")
        if not name or not date or not location:
            flash("Enter name, date, and description.", "error")
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
        db.execute("INSERT INTO tournaments (name, description, date, location) VALUES (?, ?, ?, ?)", (name, description, formatted_date, location))
        db.commit()
        flash("Tournament created.", "success")
        return redirect(url_for("tournaments_list"))


@app.route("/tournaments/<int:tid>/join", methods=["POST"])
def tournament_join(tid):
    if not session.get("user_id"):
        flash("Please log in to join a tournament.", "error")
        return redirect(url_for("login"))
    db = get_db()
    user_id = session["user_id"]
    # Ensure tournament exists
    tour = db.execute("SELECT id FROM tournaments WHERE id = ?", (tid,)).fetchone()
    if not tour:
        flash("Tournament not found.", "error")
        return redirect(url_for("tournaments_list"))
    # Prevent joining same tournament twice
    existing = db.execute(
        "SELECT id FROM participants WHERE tournament_id = ? AND user_id = ?",
        (tid, user_id)
    ).fetchone()
    if existing:
        flash("You have already joined this tournament.", "info")
        return redirect(url_for("tournament_view", tid=tid))
    # Insert participant using session username (fallback to user_id)
    name = session.get("username") or f"user{user_id}" # TODO: Change to in-game username?
    try: 
        db.execute(
            "INSERT INTO participants (tournament_id, name, seed, user_id) VALUES (?, ?, ?, ?)",
            (tid, name, None, user_id)
        )
        db.commit()
    except sqlite3.IntegrityError as e:
        flash("You can only be in one tournament at once, please leave the other tournament to join this one.", "error")
        return redirect(url_for("tournament_view", tid=tid))
    flash("You have joined the tournament.", "success")
    return redirect(url_for("tournament_view", tid=tid))


@app.route("/tournaments/<int:tid>/leave", methods=["POST"])
def tournament_leave(tid):
    if not session.get("user_id"):
        flash("Please log in to leave a tournament.", "error")
        return redirect(url_for("login"))
    db = get_db()
    user_id = session["user_id"]
    # Ensure tournament exists
    tour = db.execute("SELECT id FROM tournaments WHERE id = ?", (tid,)).fetchone()
    if not tour:
        flash("Tournament not found.", "error")
        return redirect(url_for("tournaments_list"))
    # Find the participant row for user and tournament
    participant = db.execute(
        "SELECT id FROM participants WHERE tournament_id = ? AND user_id = ?",
        (tid, user_id)
    ).fetchone()
    if not participant:
        flash("You are not a participant in this tournament.", "info")
        return redirect(url_for("tournament_view", tid=tid))
    # Delete the participant row
    db.execute("DELETE FROM participants WHERE id = ?", (participant["id"],))
    db.commit()
    flash("You have left the tournament.", "success")
    return redirect(url_for("tournament_view", tid=tid))


@app.route("/tournaments/<int:tid>", methods=["GET", "POST"])
def tournament_view(tid):
    db = get_db()
    tour = db.execute("SELECT id, name, description, date, location FROM tournaments WHERE id = ?", (tid,)).fetchone()
    if not tour:
        flash("Tournament not found.", "error")
        return redirect(url_for("tournaments_list"))
    # Load participants
    part_rows = db.execute(
        "SELECT id, name, seed, user_id FROM participants WHERE tournament_id = ? ORDER BY seed ASC",
        (tid,)
    ).fetchall()
    participants = [(r["id"], r["name"], r["seed"], r["user_id"]) for r in part_rows]
    # Determine whether current user has joined
    joined = False
    current_user_id = session.get("user_id")
    if current_user_id:
        for r in part_rows:
            if r["user_id"] == current_user_id:
                joined = True
                break
    # Generate bracket if requested
    if request.args.get("generate") == "1":
        db.execute("DELETE FROM matches WHERE tournament_id = ?", (tid,))
        rounds = create_bracket([(r[0], r[1], r[2]) for r in participants])
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
    return render_template("tournaments/view.html",
                           tournament=tour,
                           participants=participants,
                           rounds=rounds,
                           joined=joined)


@app.route("/tournaments/<int:tid>/delete", methods=["POST"])
def tournament_delete(tid):
    # Check admin
    if not session.get("is_admin"):
        flash("Admin privileges required to delete tournaments.", "error")
        return redirect(url_for("tournament_view", tid=tid))
    db = get_db()
    # Ensure tournament exists
    tour = db.execute("SELECT id FROM tournaments WHERE id = ?", (tid,)).fetchone()
    if not tour:
        flash("Tournament not found.", "error")
        return redirect(url_for("tournaments_list"))
    try:
        # Delete matches for tournament
        db.execute("DELETE FROM matches WHERE tournament_id = ?", (tid,))
        # Delete participants for tournament
        db.execute("DELETE FROM participants WHERE tournament_id = ?", (tid,))
        # Delete tournament
        db.execute("DELETE FROM tournaments WHERE id = ?", (tid,))
        db.commit()
    except Exception as e:
        db.rollback()
        app.logger.exception("Error deleting tournament %s: %s", tid, e)
        flash("Could not delete tournament. Contact an admin.", "error")
        return redirect(url_for("tournament_view", tid=tid))
    flash("Tournament deleted.", "success")
    return redirect(url_for("tournaments_list"))


@app.route("/tournaments/<int:tid>/end", methods=["POST"])
def tournament_end(tid):
    pass


@app.route("/leaderboard")
def leaderboard():
    # Get top ten
    db = get_db()
    top_rows = db.execute(
        "SELECT username, pfp, rarity, cr_username, player_tag, points FROM users ORDER BY points DESC LIMIT 10"
    ).fetchall()
    # Convert to dicts and assign rank (ties share rank)
    top = []
    for player in top_rows:
        rank_row = db.execute("SELECT COUNT(*) AS cnt FROM users WHERE points > ?", (player["points"],)).fetchone()
        rank = rank_row["cnt"] + 1
        top.append({"rank": rank, "pfp": player["pfp"], "rarity": player["rarity"], "username": player["username"], "cr_username": player["cr_username"], "player_tag": player["player_tag"], "points": player["points"]})
    # Get current user's ranking
    current_user = None
    user_row = None
    user_id = session.get("user_id")
    if user_id:
        rank_row = db.execute("SELECT COUNT(*) AS cnt FROM users WHERE points > ?", (session.get("points"),)).fetchone()
        rank = rank_row["cnt"] + 1
        current_user = {"rank": rank, "pfp": session.get("pfp"), "rarity": session.get("rarity"), "username": session.get("username"), "cr_username": session.get("cr_username"), "player_tag": session.get("player_tag"), "points": session.get("points")}
    return render_template(
        "leaderboard.html",
        top=top,
        you=current_user,
    )
    return render_template("leaderboard.html")    


if __name__ == "__main__":
    if not DATABASE.exists():
        print("Database not found. Initialize with: python init_db.py")
    app.run(debug=True)
