# /var/www/html/flaskapp/app.py
from flask import Flask, render_template_string, request
import requests
import sys
import traceback

app = Flask(__name__)

API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImU1YzBhYzg4LTgyY2EtNDgzYi05MjZjLTJhNzZmOWJjYWExNCIsImlhdCI6MTc2MTkyNzIzOSwic3ViIjoiZGV2ZWxvcGVyL2ZiYmQwZDM3LTdjMGItNWE4NC01MzRhLThlNWU2MjVmMTg5MSIsInNjb3BlcyI6WyJyb3lhbGUiXSwibGltaXRzIjpbeyJ0aWVyIjoiZGV2ZWxvcGVyL3NpbHZlciIsInR5cGUiOiJ0aHJvdHRsaW5nIn0seyJjaWRycyI6WyIzNS4xOTAuMTU4LjEwMiJdLCJ0eXBlIjoiY2xpZW50In1dfQ.jkbypj-LMpAXYWFyefbiDfZ1xvBp4wcANuCdWWethzDtbdsv7WsmborJP33YQSbfzF8A8GdMRUvuTZIurg5YBA"  # <-- put your token here

HTML_PAGE = """
<!DOCTYPE html>
<html>
  <head>
    <title>Clash Royale Player Stats</title>
    <style>
      body {
        font-family: Arial, sans-serif;
        background: #0f0f0f;
        color: white;
        text-align: center;
        padding: 40px;
      }
      input { padding: 10px; font-size: 16px; border-radius: 6px; border: none; }
      button { padding: 10px 20px; font-size: 16px; border-radius: 6px; border: none; background-color: #007bff; color: white; cursor: pointer; }
      .stats { text-align:left; background:#1a1a1a; padding:20px; border-radius:10px; display:inline-block; margin-top:20px; width:60%; }
      h2 { color:#00ff99; }
      .error { color:#ff6666; margin-top:20px; }
    </style>
  </head>
  <body>
    <h1>Clash Royale Player Lookup</h1>
    <form method="POST">
      <input type="text" name="tag" placeholder="Enter player tag (e.g. JVGPUV20)" required>
      <button type="submit">Search</button>
    </form>

    {% if player %}
      <h2>Player Stats for {{ player.tag }}</h2>
      <div class="stats">
        <p><strong>Trophies:</strong> {{ player.trophies }}</p>
        <p><strong>Wins:</strong> {{ player.wins }}</p>
        <p><strong>Three-Crown Wins:</strong> {{ player.threeCrownWins }}</p>
        <p><strong>Total Donations:</strong> {{ player.totalDonations }}</p>
        <p><strong>Total Experience Points:</strong> {{ player.totalExpPoints }}</p>
        <p><strong>Tournament Battles:</strong> {{ player.tournamentBattleCount }}</p>
        <p><strong>Tournament Cards Won:</strong> {{ player.tournamentCardsWon }}</p>
        <p><strong>War Day Wins:</strong> {{ player.warDayWins }}</p>
      </div>
    {% elif error %}
      <div class="error">{{ error }}</div>
    {% endif %}
  </body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        tag = request.form.get('tag', '').strip().upper().replace('#', '')
        if not tag:
            return render_template_string(HTML_PAGE, player=None, error="Please enter a player tag.")
        url = f"https://api.clashroyale.com/v1/players/%23{tag}"
        headers = {"Authorization": f"Bearer {API_KEY}"}

        try:
            resp = requests.get(url, headers=headers, timeout=10)
        except Exception as e:
            # Print traceback to Apache error log (visible with sudo tail -n)
            traceback.print_exc(file=sys.stderr)
            return render_template_string(HTML_PAGE, player=None, error="Network error while contacting Clash Royale API.")

        if resp.status_code != 200:
            # Log response for debugging
            try:
                sys.stderr.write(f"Clash API returned status {resp.status_code}: {resp.text[:400]}\n")
            except Exception:
                pass
            return render_template_string(HTML_PAGE, player=None, error=f"Player not found or API error (status {resp.status_code}).")

        try:
            player_data = resp.json()
        except Exception:
            traceback.print_exc(file=sys.stderr)
            return render_template_string(HTML_PAGE, player=None, error="Invalid JSON received from API.")

        # Build filtered dict (use .get safely)
        filtered = {
            "tag": player_data.get("tag"),
            "threeCrownWins": player_data.get("threeCrownWins"),
            "totalDonations": player_data.get("totalDonations"),
            "totalExpPoints": player_data.get("totalExpPoints"),
            "tournamentBattleCount": player_data.get("tournamentBattleCount"),
            "tournamentCardsWon": player_data.get("tournamentCardsWon"),
            "trophies": player_data.get("trophies"),
            "warDayWins": player_data.get("warDayWins"),
            "wins": player_data.get("wins"),
        }

        return render_template_string(HTML_PAGE, player=filtered, error=None)

    return render_template_string(HTML_PAGE, player=None, error=None)


# Expose application for mod_wsgi
application = app

# If you run directly for testing:
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

