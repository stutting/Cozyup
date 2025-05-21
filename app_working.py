import os, asyncio, datetime as dt
from dateutil import tz
from dotenv import load_dotenv
from icalendar import Calendar
from flask import Flask, render_template, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
import requests

try:
    from cozi import Cozi
except ImportError:
    Cozi = None

load_dotenv("settings.env")
ICS_URL   = os.getenv("COZI_ICS_URL")
REFRESH   = 5
HORIZON   = 14

app = Flask(__name__)
data = {"events": [], "lists": {}, "updated": None}

def parse_ical(text: str):
    now = dt.datetime.now(tz=tz.tzlocal())
    horizon = now + dt.timedelta(days=HORIZON)
    cal = Calendar.from_ical(text)
    upcoming = []

    for comp in cal.walk("vevent"):
        start = comp.decoded("dtstart")
        if isinstance(start, dt.date) and not isinstance(start, dt.datetime):
            start = dt.datetime.combine(start, dt.time.min).replace(tzinfo=tz.tzlocal())
        if now <= start <= horizon:
            all_day = comp.get("dtstart").params.get("VALUE") == "DATE"
            upcoming.append({
                "day": start.strftime("%a %b %d"),
                "time": "" if all_day else start.strftime("%I:%M %p").lstrip("0"),
                "title": str(comp.get("summary"))
            })

    return sorted(upcoming, key=lambda e: (e["day"], e["time"]))

async def fetch_lists():
    if not Cozi or not os.getenv("COZI_EMAIL"):
        return {}
    cz = Cozi(os.getenv("COZI_EMAIL"), os.getenv("COZI_PASSWORD"))
    await cz.login()
    raw = await cz.get_lists()
    return {
        lst.get("title", f"Untitled-{i}"): lst.get("items", [])
        for i, lst in enumerate(raw)
        if lst.get("listType") in ("shopping", "todo")
    }

def refresh():
    try:
        print("Refreshing Cozi data...")
        ics = requests.get(ICS_URL, timeout=10).text
        events = parse_ical(ics)
        lists = asyncio.run(fetch_lists()) if Cozi else {}
        data.update({"events": events, "lists": lists, "updated": dt.datetime.now(tz=tz.tzlocal())})
        print(f"→ {len(events)} events, {len(lists)} lists loaded at {data['updated']:%Y-%m-%d %H:%M}")
    except Exception as e:
        print("Refresh failed:", e)

scheduler = BackgroundScheduler(daemon=True)
scheduler.add_job(refresh, "interval", minutes=REFRESH)
scheduler.start()
refresh()

@app.route("/")
def dashboard():
    return render_template("dashboard.html", **data)

@app.route("/calendar")
def calendar_view():
    return render_template("calendar.html")

@app.route("/events.json")
def events_json():
    try:
        ics = requests.get(ICS_URL, timeout=10).text
        cal = Calendar.from_ical(ics)
        events = []
        for comp in cal.walk("vevent"):
            start = comp.decoded("dtstart")
            end = comp.decoded("dtend", start)  # fallback to start if no end provided

            # Cozi may send dtstart as datetime.date — normalize it
            if isinstance(start, dt.date) and not isinstance(start, dt.datetime):
                start = dt.datetime.combine(start, dt.time.min).replace(tzinfo=tz.tzlocal())
            if isinstance(end, dt.date) and not isinstance(end, dt.datetime):
                end = dt.datetime.combine(end, dt.time.min).replace(tzinfo=tz.tzlocal())

            events.append({
                "title": str(comp.get("summary")),
                "start": start.isoformat(),
                "end": end.isoformat(),
                "allDay": comp.get("dtstart").params.get("VALUE") == "DATE"
            })
        return jsonify(events)
    except Exception as e:
        print("Event JSON feed failed:", e)
        return jsonify([])



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
