# WoW Auction House Sniper

Watches World of Warcraft auction house prices via the
[Undermine Exchange API](https://undermine.exchange/api.html) and alerts you
when an item drops to or below a price you set.

## Setup

1. Get an API key:
   - Sign in with Patreon at https://undermine.exchange/ (free account is fine)
   - Reveal your key on https://undermine.exchange/api.html
2. Put it in `.env` (already git-ignored):
   ```
   UNDERMINE_API_KEY=your_key_here
   ```
3. Install dependencies:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\pip install -r requirements.txt
   ```

## Usage

### One-off price check

Commodities (stackable trade goods — ore, herbs, cloth, etc.) are priced
region-wide, not per realm:

```powershell
.\.venv\Scripts\python.exe sniper.py check --item-id 251285 --region eu --commodity
```

Non-commodity items (gear, mounts, pets, etc.) are priced per realm. Use any
realm slug in the connected-realm group (e.g. `drakthul` and
`burning-blade` share one EU auction house):

```powershell
.\.venv\Scripts\python.exe sniper.py check --item-id 118852 --region eu --realm drakthul
```

Find item IDs on [Wowhead](https://www.wowhead.com) — the ID is in the item's
URL, e.g. `wowhead.com/item=251285/petrified-root` → `251285`.

### Watch mode (continuous sniping)

Edit `watchlist.yaml` to add items and your target buy price, then run:

```powershell
.\.venv\Scripts\python.exe sniper.py watch --interval 300
```

This polls every 5 minutes (adjustable) and prints `<<< DEAL!` plus a
terminal bell whenever a watched item's price is at or below your
`max_price_gold`.

> Undermine's underlying data refreshes roughly once an hour (matching
> Blizzard's own AH snapshot cadence), so polling much faster than that
> won't get you newer data — it just spends your API rate limit budget
> faster (3,000 points/hour per key).

## Files

| File | Purpose |
|---|---|
| `undermine_client.py` | Thin wrapper around the Undermine Exchange API |
| `sniper.py` | CLI: `check` (one-off) and `watch` (polling loop) |
| `watchlist.yaml` | Items you want to snipe, with target prices |
| `.env` | Your API key (never committed) |

## Notes

- Prices are always returned in copper by the API; the tool converts to
  gold/silver/copper automatically.
- No API key is ever printed by this tool.
