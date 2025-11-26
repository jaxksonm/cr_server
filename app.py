from flask import Flask, render_template_string
import requests

app = Flask(__name__)

API_KEY = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzUxMiIsImtpZCI6IjI4YTMxOGY3LTAwMDAtYTFlYi03ZmExLTJjNzQzM2M2Y2NhNSJ9.eyJpc3MiOiJzdXBlcmNlbGwiLCJhdWQiOiJzdXBlcmNlbGw6Z2FtZWFwaSIsImp0aSI6ImU1YzBhYzg4LTgyY2EtNDgzYi05MjZjLTJhNzZmOWJjYWExNCIsImlhdCI6MTc2MTkyNzIzOSwic3ViIjoiZGV2ZWxvcGVyL2ZiYmQwZDM3LTdjMGItNWE4NC01MzRhLThlNWU2MjVmMTg5MSIsInNjb3BlcyI6WyJyb3lhbGUiXSwibGltaXRzIjpbeyJ0aWVyIjoiZGV2ZWxvcGVyL3NpbHZlciIsInR5cGUiOiJ0aHJvdHRsaW5nIn0seyJjaWRycyI6WyIzNS4xOTAuMTU4LjEwMiJdLCJ0eXBlIjoiY2xpZW50In1dfQ.jkbypj"
PLAYER_TAG = "#JVGPUV20"

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Clash Royale Player Stats</title>
</head>
<body>
    <h1>Clash Royale Player Stats</h1>
    {% if error %}
        <p style="color:red;">{{ error }}</p>
    {% else %}
        <p>Name: {{ data['name'] }} (#{{ player_tag }})</p>
        <p>Trophies: {{ data['trophies'] }}</p>
        <p>Best Trophies: {{ data['bestTrophies'] }}</p>
        <p>Arena: {{ data['arena']['name'] }}</p>
        <p>Clan: {{ data['clan']['name'] if data.get('clan') else 'None' }}</p>
    {% endif %}
</body>
</html>
"""

@app.route("/")
def index():
    url = f"https://api.clashroyale.com/v1/players/%23{PLAYER_TAG}"
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        data = response.json()
        return render_template_string(TEMPLATE, data=data, player_tag=PLAYER_TAG, error=None)
    except requests.RequestException as e:
        return render_template_string(TEMPLATE, data=None, player_tag=PLAYER_TAG, error=str(e))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

