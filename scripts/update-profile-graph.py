"""Refresh the profile contribution graph using GitHub's public profile API.

Run with the GitHub CLI authenticated, or GH_TOKEN set by GitHub Actions.
No third-party Python dependencies are required.
"""
from datetime import datetime, timezone, timedelta
from pathlib import Path
import json
import math
import subprocess
import html

LOGIN = "yateshr"
query = '''query {
  user(login: "yateshr") {
    contributionsCollection {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}'''
response = subprocess.run(["gh", "api", "graphql", "-f", "query=" + query], text=True, capture_output=True)
if response.returncode:
    raise SystemExit("GitHub contribution lookup failed; retaining the existing graph.")
payload = json.loads(response.stdout)
if payload.get("errors"):
    raise SystemExit("GitHub returned a contribution-query error; retaining the existing graph.")
weeks = payload["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
days = sorted((day for week in weeks for day in week["contributionDays"]), key=lambda day: day["date"])[-31:]
if len(days) < 2:
    raise SystemExit("Not enough contribution dates; retaining the existing graph.")
width, height = 960, 310
left, right, top, bottom = 62, 932, 65, 246
peak = max(day["contributionCount"] for day in days)
maximum = max(4, math.ceil(peak / 4) * 4)
svg = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
       '<title id="title">Yatesh Rohit — contribution activity</title>',
       '<desc id="desc">GitHub contribution counts for the latest 31 calendar days. Values come from the GitHub contribution calendar.</desc>',
       '<rect x="1" y="1" width="958" height="308" rx="12" fill="#0d1117" stroke="#30363d"/>',
       '<g font-family="Segoe UI,Arial,sans-serif">',
       '<text x="32" y="36" fill="#00d9ff" font-size="20" font-weight="600">Contribution activity</text>',
       '<text x="928" y="35" text-anchor="end" fill="#8b949e" font-size="13">Last 31 calendar days</text>']
for step in range(5):
    y = bottom - (bottom - top) * step / 4
    svg += [f'<path d="M{left} {y:.1f}H{right}" stroke="#21262d" stroke-width="1"/>',
            f'<text x="48" y="{y+4:.1f}" text-anchor="end" fill="#8b949e" font-size="11">{maximum*step//4}</text>']
points = []
for index, day in enumerate(days):
    x = left + (right - left) * index / (len(days) - 1)
    y = bottom - (bottom - top) * day["contributionCount"] / maximum
    points.append((x, y, day))
coordinates = " ".join(f"{x:.1f},{y:.1f}" for x, y, _ in points)
svg.append(f'<polygon points="{left},{bottom} {coordinates} {right},{bottom}" fill="#00d9ff" fill-opacity=".055"/>')
svg.append(f'<polyline points="{coordinates}" fill="none" stroke="#00d9ff" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/>')
for index, (x, y, day) in enumerate(points):
    count = day["contributionCount"]
    label = html.escape(f"{day['date']}: {count} contributions")
    svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.5" fill="#ffd700"><title>{label}</title></circle>')
    if index in [0, 5, 10, 15, 20, 25, len(days)-1]:
        text = datetime.fromisoformat(day["date"]).strftime("%d %b")
        svg.append(f'<text x="{x:.1f}" y="268" text-anchor="middle" fill="#8b949e" font-size="11">{text}</text>')
updated = datetime.now(timezone(timedelta(hours=5, minutes=30))).strftime("%d %b %Y")
svg += [f'<text x="32" y="294" fill="#8b949e" font-size="11">GitHub contribution calendar · Updated {updated} IST</text>', '</g></svg>']
output = Path(__file__).resolve().parents[1] / "assets/contribution-graph.svg"
output.write_text("\n".join(svg)+"\n", encoding="utf-8")
print(f"Updated {output.name}: {len(days)} days, {sum(day['contributionCount'] for day in days)} contributions")
