"""J. Cole Ticketmaster watcher -> WhatsApp (via CallMeBot).

Runs on GitHub Actions. Configuration comes from environment variables /
repository secrets, see README.md.
"""
import json
import os
import sys
import time
import urllib.parse
import urllib.request

TM_API_KEY = os.environ["TM_API_KEY"]
PHONE = os.environ["CALLMEBOT_PHONE"]        # e.g. +27821234567
CM_KEY = os.environ["CALLMEBOT_KEY"]

KEYWORD = os.environ.get("ARTIST") or "J. Cole"
COUNTRY = os.environ.get("COUNTRY_CODE") or "ZA"
CITY = os.environ.get("CITY") or ""
DATE = os.environ.get("SHOW_DATE") or ""
WANTED = [w.strip().lower() for w in (os.environ.get("WANTED_WORDS") or
          "standing,general admission,ga,floor,pit").split(",")]
HEARTBEAT_HOURS = float(os.environ.get("HEARTBEAT_HOURS") or 24)

STATE_FILE = "state.json"
sent_any = False


def whatsapp(text):
    global sent_any
    url = ("https://api.callmebot.com/whatsapp.php?"
           + urllib.parse.urlencode({"phone": PHONE, "text": text, "apikey": CM_KEY}))
    with urllib.request.urlopen(url, timeout=30) as r:
        print("WhatsApp response:", r.status)
    sent_any = True
    time.sleep(3)  # be gentle with CallMeBot's rate limit


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
        "prices": [f'{p.get("type")}: {p.get("currency", "")} {p.get("min")}-{p.get("max")}'
                   for p in prices],
        "keywords": found,
        "url": ev.get("url"),
    }


def details(s):
    price = "; ".join(s["prices"]) if s["prices"] else "no price info"
    return f"Status: {s['status']}\nPrices: {price}\n{s['url']}"


def load_state():
    try:
        with open(STATE_FILE) as f:
            data = json.load(f)
    except FileNotFoundError:
        return {}, 0
    if "events" in data:                      # current format
        return data["events"], data.get("last_message", 0)
    return data, 0                            # older format


def main():
    if os.environ.get("TEST_MESSAGE") == "1":
        whatsapp("Test OK: your J. Cole ticket bot can reach your WhatsApp.")
        return

    old, last_message = load_state()
    first_run = not old
    new, alerts = {}, []

    for ev in fetch_events():
        s = snapshot(ev)
        new[ev["id"]] = s
        prev = old.get(ev["id"])
        label = f'{s["name"]} - {s["venue"]} - {s["date"]}'
        if prev is None:
            alerts.append(f"NEW LISTING: {label}\n{details(s)}")
            continue
        if s["status"] == "onsale" and prev["status"] != "onsale":
            alerts.append(f"TICKETS ON SALE: {label}\n{details(s)}")
        elif s["status"] != prev["status"]:
            alerts.append(f"STATUS CHANGED {prev['status']} -> {s['status']}: {label}\n{details(s)}")
        if s["keywords"] and s["keywords"] != prev["keywords"]:
            alerts.append(f"STANDING/GA HINT ({', '.join(s['keywords'])}): {label}\n{details(s)}")
        if s["prices"] != prev["prices"]:
            alerts.append(f"PRICES CHANGED: {label}\nWas: {'; '.join(prev['prices']) or 'none'}\n{details(s)}")

    if first_run and not new:
        alerts.append(f"Bot is running but found 0 events for '{KEYWORD}' "
                      f"({COUNTRY} {CITY} {DATE}). Check your settings.")

    for a in alerts:
        whatsapp(a)

    # Daily "still alive" message when nothing else was sent
    hours_quiet = (time.time() - last_message) / 3600
    if not sent_any and hours_quiet >= HEARTBEAT_HOURS:
        lines = [f'{s["name"]} ({s["date"]}): {s["status"]}' for s in new.values()]
        whatsapp("Still watching, nothing new in the last "
                 f"{int(HEARTBEAT_HOURS)}h.\n" + ("\n".join(lines) or "No events found."))

    print(f"{len(new)} events watched, {len(alerts)} alerts sent")
    with open(STATE_FILE, "w") as f:
        json.dump({"events": new,
                   "last_message": time.time() if sent_any else last_message},
                  f, indent=1, sort_keys=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("ERROR:", e, file=sys.stderr)
        sys.exit(1)
