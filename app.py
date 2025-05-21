import os
import requests
from datetime import datetime, timedelta
import random
from flask import Flask, jsonify, render_template
from apscheduler.schedulers.background import BackgroundScheduler
from ics import Calendar

app = Flask(__name__)

cozi_ics_url = "https://rest.cozi.com/api/ext/1103/a9c09367-615e-45ae-9fa6-d24347cb773e/icalendar/feed/feed.ics"
outlook_ics_url = "https://outlook.office365.com/owa/calendar/6ff3479a18be456f837f24ce8c3338e7@ntc.edu/3241ea8fdf7d42c681382d964d95858711498164704385653839/calendar.ics"

combined_events = []

def refresh_events():
    global combined_events
    combined_events = []

    for url, label in [(cozi_ics_url, ""), (outlook_ics_url, "NTC: ")]:
        try:
            resp = requests.get(url)
            cal = Calendar(resp.text)
            for event in cal.events:
                if event.begin:
                    combined_events.append({
                        "title": (label + event.name) if event.name else "Untitled",
                        "start": event.begin.datetime.isoformat(),
                        "end": event.end.datetime.isoformat() if event.end else None,
                        "allDay": event.all_day,
                        "source": "outlook" if label else "cozi"
                    })
        except Exception as e:
            print(f"Error loading events from {url}: {e}")

scheduler = BackgroundScheduler()
scheduler.add_job(refresh_events, 'interval', minutes=5)
scheduler.start()
refresh_events()

@app.route("/")
def dashboard():
    global combined_events

    now = datetime.now()
    current_day = now.strftime('%A')
    current_date = now.strftime('%B %d, %Y')

    # Fetch a random joke
    try:
        joke_resp = requests.get("https://official-joke-api.appspot.com/random_joke", timeout=5).json()
        joke = f"{joke_resp['setup']} {joke_resp['punchline']}"
    except:
        joke = "Why don't scientists trust atoms? Because they make up everything!"

    today_events = []
    week_events_grouped = {}

    this_week = now + timedelta(days=7)

    for e in combined_events:
        try:
            start_dt = datetime.fromisoformat(e["start"])
        except:
            continue

        if start_dt.date() == now.date():
            today_events.append({
                "title": e["title"],
                "start": start_dt,
                "end": datetime.fromisoformat(e["end"]) if e.get("end") else None,
                "allDay": e.get("allDay", False)
            })
        elif now.date() < start_dt.date() <= this_week.date():
            label = start_dt.strftime('%A')
            week_events_grouped.setdefault(label, []).append({
                "title": e["title"],
                "start": start_dt,
                "end": datetime.fromisoformat(e["end"]) if e.get("end") else None,
                "allDay": e.get("allDay", False)
            })

    return render_template("dashboard.html",
        current_day=current_day,
        current_date=current_date,
        joke=joke,
        today_events=today_events,
        week_events=week_events_grouped
    )



@app.route("/calendar")
def calendar_view():
    return render_template("calendar.html")

@app.route("/events.json")
def events_json():
    return jsonify(combined_events)

if __name__ == "__main__":
    app.run(debug=True)
