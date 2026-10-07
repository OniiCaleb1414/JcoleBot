"""J. Cole Ticketmaster watcher -> WhatsApp (via CallMeBot).

Runs on GitHub Actions. Configuration comes from environment variables /
repository secrets, see README.md.
"""
import json
import os
import sys
import urllib.parse
import urllib.request

TM_API_KEY = os.environ["TM_API_KEY"]
PHONE = os.environ["CALLMEBOT_PHONE"]        # e.g. +27821234567
CM_KEY = os.environ["CALLMEBOT_KEY"]

KEYWORD = os.environ.get("ARTIST", "J. Cole")
COUNTRY = os.environ.get("COUNTRY_CODE", "US")   # ISO code, e.g. US, GB, CA
CITY = os.environ.get("CITY", "")                # optional, e.g. Atlanta
DATE = os.environ.get("SHOW_DATE", "")           # optional YYYY-MM-DD
WANTED = [w.strip().lower() for w in os.environ.get(
    "WANTED_WORDS", "standing,general admission,ga,floor,pit").split(",")]

STATE_FILE = "state.json"


def whatsapp(text):
    url = ("https://api.callmebot.com/whatsapp.php?"
           + urllib.parse.urlencode({"phone": PHONE, "text": text, "apikey": CM_KEY}))
    with urllib.request.urlopen(url, timeout=30) as r:
        print("WhatsApp response:", r.status)


def fetch_events():
    params = {"apikey": TM_API_KEY, "keyword": KEYWORD,
              "countryCode": COUNTRY, "size": 50, "sort": "date,asc"}
    if CITY:
        params["city"] = CITY
    if DATE:
        params["startDateTime"] = f"{DATE}T00:00:00Z"
        params["endDateTime"] = f"{DATE}T23:59:59Z"
    url = "https://app.ticketmaster.com/discovery/v2/events.json?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        data = json.load(r)
    return data.get("_embedded", {}).get("events", [])


def snapshot(ev):
    text = " ".join(str(ev.get(k, "")) for k in ("name", "info", "pleaseNote")).lower()
    prices = ev.get("priceRanges", [])
    price_text = " ".join(str(p.get("type", "")) for p in prices).lower()
    found = sorted({w for w in WANTED if w and w in (text + " " + price_text)})
    venue = (ev.get("_embedded", {}).get("venues") or [{}])[0].get("name", "?")
    return {
        "name": ev.get("name"),
        "date": ev.get("dates", {}).get("start", {}).get("localDate", "?"),
        "venue": venue,
        "status": ev.get("dates", {}).get("status", {}).get("code", "?"),
        "prices": [f'{p.get("type")}:{p.get("min")}-{p.get("max")}' for p in prices],
        "keywords": found,
        "url": ev.get("url"),
    }


def main():
    if os.environ.get("TEST_MESSAGE") == "1":
        whatsapp("Test OK: your J. Cole ticket bot can reach your WhatsApp.")
        return

    try:
        with open(STATE_FILE) as f:
            old = json.load(f)
    except FileNotFoundError:
        old = {}

    new = {}
    alerts = []
    for ev in fetch_events():
        s = snapshot(ev)
        new[ev["id"]] = s
        prev = old.get(ev["id"])
        label = f'{s["name"]} - {s["venue"]} - {s["date"]}'
        if prev is None:
            alerts.append(f"NEW LISTING: {label}\nStatus: {s['status']}\n{s['url']}")
        else:
            if s["status"] == "onsale" and prev["status"] != "onsale":
                alerts.append(f"TICKETS ON SALE: {label}\n{s['url']}")
            if s["keywords"] != prev["keywords"] and s["keywords"]:
                alerts.append(f"Standing/GA hint ({', '.join(s['keywords'])}): {label}\n{s['url']}")
            if s["prices"] != prev["prices"] and s["status"] == "onsale":
                alerts.append(f"Ticket prices changed: {label}\n{s['url']}")

    if not new and not old:
        alerts.append(f"Bot is running but found 0 events for '{KEYWORD}' "
                      f"({COUNTRY} {CITY} {DATE}). Ticketmaster's API may not "
                      "cover this show, or the settings need a tweak.")

    for a in alerts:
        whatsapp(a)
    print(f"{len(new)} events watched, {len(alerts)} alerts sent")

    with open(STATE_FILE, "w") as f:
        json.dump(new, f, indent=1, sort_keys=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        sys.exit(1)
