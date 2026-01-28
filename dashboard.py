from flask import Flask, render_template_string, jsonify
import subprocess
import re
import time
import threading
from datetime import datetime

app = Flask(__name__)

# Global storage for data points
data_points = []

# HTML Template for dashboard
html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Invisible Watchdogs Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            background-color: #0d1117;
            color: #c9d1d9;
            text-align: center;
        }
        .chart-container {
            width: 80%;
            margin: 50px auto;
            background: #161b22;
            padding: 20px;
            border-radius: 15px;
            box-shadow: 0 0 15px rgba(0,0,0,0.5);
        }
        h1 { color: #58a6ff; }
    </style>
</head>
<body>
    <h1>Invisible Watchdogs: Wi-Fi Sensing Dashboard</h1>
    <p>Monitoring RSSI fluctuations to detect motion</p>
    <div class="chart-container">
        <canvas id="signalChart"></canvas>
    </div>

    <script>
        const ctx = document.getElementById('signalChart').getContext('2d');
        const chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Signal Strength (%)',
                    data: [],
                    borderColor: '#58a6ff',
                    backgroundColor: 'rgba(88,166,255,0.1)',
                    borderWidth: 2,
                    tension: 0.2,
                    fill: true,
                }]
            },
            options: {
                scales: {
                    y: { min: 0, max: 100, title: { display: true, text: 'Signal (%)', color: '#c9d1d9' }},
                    x: { title: { display: true, text: 'Time', color: '#c9d1d9' }}
                },
                plugins: { legend: { labels: { color: '#c9d1d9' }}}
            }
        });

        async function fetchData() {
            const res = await fetch('/data');
            const json = await res.json();
            chart.data.labels = json.timestamps;
            chart.data.datasets[0].data = json.signals;
            chart.update();
        }
        setInterval(fetchData, 1000);
    </script>
</body>
</html>
"""

def get_rssi():
    """Fetch Wi-Fi signal strength using Windows netsh command."""
    try:
        output = subprocess.check_output(["netsh", "wlan", "show", "interfaces"], text=True)
        match = re.search(r"Signal\s*:\s*(\d+)", output)
        if match:
            return int(match.group(1))
    except Exception:
        pass
    return None

def sense_wifi():
    """Continuously sense Wi-Fi and store data points."""
    start = time.time()
    while True:
        rssi = get_rssi()
        if rssi is not None:
            t = round(time.time() - start, 1)
            data_points.append((t, rssi))
            if len(data_points) > 100:
                data_points.pop(0)
        time.sleep(1)

@app.route('/')
def home():
    return render_template_string(html_template)

@app.route('/data')
def data():
    timestamps = [str(t) for t, _ in data_points]
    signals = [s for _, s in data_points]
    return jsonify({"timestamps": timestamps, "signals": signals})

if __name__ == '__main__':
    threading.Thread(target=sense_wifi, daemon=True).start()
    print("Dashboard running at: http://127.0.0.1:5000")
    app.run(debug=False)
