# WoW Auction House Sniper

Watches World of Warcraft auction house prices and alerts you when an item drops
to or below your target price.

**Two data sources supported — Undermine Exchange is the default/main source:**

| Source | What it gives you | Requires |
|---|---|---|
| `undermine` *(default)* | Aggregated current market price via [Undermine Exchange API](https://undermine.exchange/api.html) | Undermine API key (free Patreon) |
| `blizzard` | Raw live auction listings directly from Blizzard | Battle.net developer app |

## Setup

### 1. Copy `.env.example` to `.env`

```
cp .env.example .env
```

### 2. Add credentials

**Undermine Exchange (needed for the default source):**
- Sign in with Patreon at https://undermine.exchange/ (free account is fine)
- Reveal your key at https://undermine.exchange/api.html
- Set `UNDERMINE_API_KEY` in `.env`

**Blizzard API (only needed if you use `--source blizzard`):**
- Create an application at https://develop.battle.net/ (no special scopes needed)
- Set `BLIZZARD_CLIENT_ID` and `BLIZZARD_CLIENT_SECRET` in `.env`

### 3. Install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt
```

## Usage

### One-off price check

Commodities (stackable trade goods — ore, herbs, cloth, etc.) are priced region-wide:

```powershell
# Undermine (default)
.\.venv\Scripts\python sniper.py check --item-id 251285 --region eu --commodity

# Blizzard source
.\.venv\Scripts\python sniper.py check --item-id 251285 --region eu --commodity --source blizzard
```

Non-commodity items (gear, mounts, pets) are per realm:

```powershell
.\.venv\Scripts\python sniper.py check --item-id 118852 --region eu --realm drakthul
```

Find item IDs on [Wowhead](https://www.wowhead.com) — the ID is in the URL,
e.g. `wowhead.com/item=251285/petrified-root` → `251285`.

### Watch mode (continuous sniping)

Edit `watchlist.yaml` to add items and your target buy prices, then run:

```powershell
.\.venv\Scripts\python sniper.py watch --interval 300
```

This polls every 5 minutes and prints `<<< DEAL!` plus a terminal bell whenever a
watched item's price is at or below `max_price_gold`.

To use Blizzard as the default source for the whole watchlist:

```powershell
.\.venv\Scripts\python sniper.py watch --source blizzard
```

Or set `source: blizzard` on individual items in `watchlist.yaml` to mix sources.

> **Tip:** Undermine's data refreshes roughly once an hour (matching Blizzard's AH
> snapshot cadence), so polling much faster won't get you newer data — it just burns
> your rate-limit budget (3,000 points/hour per Undermine key). Blizzard's endpoint
> also updates ~hourly.

## Files

| File | Purpose |
|---|---|
| `undermine_client.py` | Undermine Exchange API client (main/default source) |
| `blizzard_client.py` | Blizzard Game Data API client (alternative source) |
| `sniper.py` | CLI: `check` (one-off) and `watch` (polling loop) |
| `watchlist.yaml` | Items to snipe with target prices and optional source override |
| `.env` | Your API credentials (never committed) |

## Notes

- Prices are always in copper internally; the tool converts to gold/silver/copper for display.
- Blizzard realm auction dumps can be large (10k+ listings). They are cached in memory
  for 5 minutes to avoid redundant fetches during a watch cycle.
- No credentials are ever printed by this tool.
