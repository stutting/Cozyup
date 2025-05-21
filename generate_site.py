import os
import requests
from datetime import datetime, timedelta, time
from icalendar import Calendar
from dateutil import tz

DAYS_AHEAD = int(os.getenv('DAYS_AHEAD', '7'))

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset='utf-8'>
<title>Family Calendar</title>
<style>
body { font-family: Arial, sans-serif; margin: 2em; }
.hidden { display: none; }
.event-day { margin-top: 1em; font-weight: bold; }
</style>
<script>
const HASH = '{hash}';
function sha256(str) {
  const buf = new TextEncoder('utf-8').encode(str);
  return crypto.subtle.digest('SHA-256', buf).then(buf => {
    return Array.from(new Uint8Array(buf)).map(x => x.toString(16).padStart(2, '0')).join('');
  });
}
async function checkPassword() {
  const pwd = document.getElementById('pwd').value;
  const digest = await sha256(pwd);
  if (digest === HASH) {
    document.getElementById('login').classList.add('hidden');
    document.getElementById('content').classList.remove('hidden');
  } else {
    alert('Incorrect password');
  }
}
</script>
</head>
<body>
<div id="login">
  <p>Please enter password:</p>
  <input type="password" id="pwd" />
  <button onclick="checkPassword()">Enter</button>
</div>
<div id="content" class="hidden">
  <h1>Family Calendar</h1>
  {content}
</div>
</body>
</html>
"""

def fetch_calendar(url):
    resp = requests.get(url)
    resp.raise_for_status()
    return Calendar.from_ical(resp.text)

def parse_events(cal):
    now = datetime.now(tz=tz.tzlocal())
    horizon = now + timedelta(days=DAYS_AHEAD)
    events = []
    seen = set()
    for comp in cal.walk('vevent'):
        start = comp.decoded('dtstart')
        if isinstance(start, datetime):
            start = start.astimezone(tz.tzlocal())
        else:
            start = datetime.combine(start, time.min).replace(tzinfo=tz.tzlocal())
        if now.date() <= start.date() <= horizon.date():
            summary = str(comp.get('summary'))
            key = (start.isoformat(), summary)
            if key in seen:
                continue
            seen.add(key)
            all_day = comp.get('dtstart').params.get('VALUE') == 'DATE'
            events.append((start, summary, all_day))
    return sorted(events, key=lambda e: e[0])

def main():
    cozi = os.getenv('COZI_ICS_URL')
    outlook = os.getenv('OUTLOOK_ICS_URL')
    pw_hash = os.getenv('SITE_PASSWORD_HASH', '')
    if not (cozi and outlook):
        raise SystemExit('Missing ICS URLs')
    events = []
    for url in (cozi, outlook):
        try:
            cal = fetch_calendar(url)
            events.extend(parse_events(cal))
        except Exception as e:
            print('Failed to load', url, e)
    events.sort(key=lambda x: x[0])
    content_parts = []
    current_day = None
    for start, summary, all_day in events:
        day_label = start.strftime('%A %b %d')
        time_label = '' if all_day else start.strftime('%I:%M %p').lstrip('0')
        if day_label != current_day:
            content_parts.append(f"<div class='event-day'>{day_label}</div>")
            current_day = day_label
        label = f"- {time_label} {summary}" if time_label else f"- {summary}"
        content_parts.append(f"<div class='event'>{label}</div>")
    html = TEMPLATE.format(content='\n'.join(content_parts), hash=pw_hash)
    with open('index.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print('index.html generated')

if __name__ == '__main__':
    main()
