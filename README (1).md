# J. Cole Ticketmaster → WhatsApp bot

Checks Ticketmaster every ~5 minutes on GitHub's servers (free) and WhatsApps you.

## What it alerts on
- A new J. Cole listing appears for your country/city/date
- A listing flips to **on sale**
- "Standing / general admission / floor / pit" wording shows up
- Ticket prices change on an on-sale event

## Setup (about 15 minutes)

### 1. Ticketmaster API key (free)
Sign up at https://developer.ticketmaster.com, create an app, copy the **Consumer Key**.

### 2. CallMeBot WhatsApp key (free)
Go to https://www.callmebot.com/blog/free-api-whatsapp-messages/ and follow the steps
(save their number in your contacts, send the activation message on WhatsApp,
they reply with your API key). Use the number shown on that page, as it can change.

### 3. GitHub repo
1. Create a **new private repo** on github.com.
2. Upload these files, keeping the folder structure:
   `bot.py` and `.github/workflows/watch.yml`.
3. **Settings → Secrets and variables → Actions → Secrets** – add:
   - `TM_API_KEY` – your Ticketmaster key
   - `CALLMEBOT_PHONE` – your number with country code, e.g. `+27821234567`
   - `CALLMEBOT_KEY` – the key CallMeBot sent you
4. Same page, **Variables** tab – add:
   - `COUNTRY_CODE` – e.g. `US`, `GB`, `CA`
   - `CITY` – e.g. `Atlanta` (optional)
   - `SHOW_DATE` – e.g. `2026-11-14` (optional)
5. **Settings → Actions → General → Workflow permissions** → choose
   *Read and write permissions* → Save.

### 4. Test
**Actions tab → Watch Ticketmaster → Run workflow**, set `test_message` to `1`.
You should get a WhatsApp message within a minute. Then run it again with `0`;
the first real run sends you a list of what it's currently watching.

## Limits to know
- Ticketmaster's free API shows event status and price ranges, **not live
  section-by-section stock**. It reliably catches new dates and on-sale
  moments, but can't confirm standing tickets are actually in stock.
- GitHub's 5-minute schedule can run late by a few minutes at busy times.
  For an on-sale rush, also set a phone alarm for the announced on-sale time.
- Ticketmaster does not sell in every country (e.g. South Africa's events are
  on Computicket), so use the country where the show actually is.
