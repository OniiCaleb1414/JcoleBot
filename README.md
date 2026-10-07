# J. Cole Ticketmaster → WhatsApp bot

Checks Ticketmaster every ~5 minutes on GitHub's servers (free) and WhatsApps you.
Set up for: **J. Cole, FNB Stadium, Johannesburg, 12 Dec 2026**.

## What it messages you about
- A new J. Cole listing appears (with status, prices and link)
- The listing's status changes (e.g. sold out → **on sale**)
- Ticket prices change (including a new price tier appearing)
- "Standing / general admission / floor / pit" wording shows up
- **Daily "still watching" message** if nothing else was sent in 24 hours,
  so silence never means the bot died

## Setup (about 15 minutes)

### 1. Ticketmaster API key (free)
Sign up at https://developer.ticketmaster.com, create an app, copy the **Consumer Key**.

### 2. CallMeBot WhatsApp key (free)
Follow https://www.callmebot.com/blog/free-api-whatsapp-messages/ (save their
number in your contacts, send the activation message on WhatsApp, they reply
with your API key). Use the number shown on that page, as it can change.

### 3. GitHub repo
1. Create a **new private repo** on github.com.
2. Upload `bot.py`, `README.md` and `.github/workflows/watch.yml`, keeping the folders.
3. **Settings → Secrets and variables → Actions → Secrets**, add:
   - `TM_API_KEY` – your Ticketmaster key
   - `CALLMEBOT_PHONE` – your number with country code, e.g. `+27821234567`
   - `CALLMEBOT_KEY` – the key CallMeBot sent you
4. Same page, **Variables** tab, add:
   - `COUNTRY_CODE` = `ZA`
   - `CITY` = `Johannesburg`
   - `SHOW_DATE` = `2026-12-12`
   - `HEARTBEAT_HOURS` = `24` (optional, how often the "still watching" message is sent)
5. **Settings → Actions → General → Workflow permissions** → *Read and write permissions* → Save.

### 4. Test
**Actions tab → Watch Ticketmaster → Run workflow**, set `test_message` to `1`.
You should get a WhatsApp within a minute. Then run it again with `0`;
the first real run messages you what it is currently watching.

## Limits to know
- **Sections are not available.** Ticketmaster's free API gives event status and
  price ranges only. It cannot show whether *standing / GA* specifically is in
  stock. The bot sends you the price tiers and link so you can open the page
  and check the seat map yourself.
- Extra tickets added to an event that stays "on sale" may not change anything
  the API shows. Also follow Big Concerts (bigconcerts.co.za) and join their
  mailing list for release announcements.
- GitHub's 5-minute schedule can run a few minutes late. For a known release time,
  also set a phone alarm.
- If you stop getting daily messages, check the Actions tab for errors
  (usually an expired CallMeBot key or a typo in a secret).
