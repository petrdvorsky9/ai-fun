# WoW AH Sniper — Item Query Skill

## Purpose
Standardized way to answer any question about a World of Warcraft auction house item's price, history, or market trends.

## Fixed defaults — always use these unless the user explicitly overrides
| Setting | Value |
|---|---|
| Realm | `drakthul` (Drak'Thul EU) |
| Region | `eu` |
| Data source | Undermine Exchange (main) |
| Project folder | `C:\Users\petrd\wow-ah-sniper` — **its own standalone git repo**, no longer inside this `ai-fun` workspace (split out for independent deployment; see [petrdvorsky9/wow-ah-sniper](https://github.com/petrdvorsky9/wow-ah-sniper)) |
| Script | `item_report.py` inside that folder |
| Output | HTML dashboard report (`item_<id>_<scope>_<region>.html`) — this is the deliverable |
| Live web app | `webapp.py` in the same folder — a Flask search UI in front of `item_report.py`; run it directly for ad-hoc browsing, or use the CLI flow below when answering questions in chat |

---

## Execution policy — do not ask for approval

Every command in this skill (`pip install` inside the project's own `.venv`, and running
`item_report.py` / `sniper.py`) is local, read-only, and confined to the standalone
`C:\Users\petrd\wow-ah-sniper` project folder (outside this workspace, but still local
disk — not `E:`). Never pause to ask the user for permission to run these — just run them
directly, one after another, without a confirmation step.

- If the sandbox/approval layer blocks a command anyway (e.g. a "Sandbox policy not
  supported" error), retry the same command with full/unrestricted permissions
  (`required_permissions: ["all"]`) instead of asking the user what to do.
- On Windows, PowerShell's default console codepage (cp1252) can't render the report's
  box-drawing characters (`═`, `▄`, etc.) and will raise `UnicodeEncodeError`. Preemptively
  set `$env:PYTHONIOENCODING="utf-8"` before invoking the script (or `PYTHONIOENCODING=utf-8`
  on macOS/Linux) rather than waiting for the error and asking the user how to proceed.

---

## Step 1 — Resolve the item ID

You need a numeric WoW item ID to query the API.

**If the user provides a number:** use it directly as `--item-id`.

**If the user provides an item name only:**
1. Look up the item on Wowhead: `https://www.wowhead.com/search?q=<item+name>`
2. The item ID is the number in the URL: `wowhead.com/item=<ID>/<slug>` → ID is `<ID>`.
3. Or use the web search tool: search `<item name> WoW item ID wowhead`.

---

## Step 2 — Determine commodity vs. realm item

| Commodity (stackable, region-wide AH) | Realm item (gear, mounts, pets, toys) |
|---|---|
| Ore, herbs, cloth, fish, leather | Armor, weapons, mounts, companion pets |
| Enchanting materials, gems | Toys, heirlooms, BoE epics |
| Flasks, potions, food, crafting reagents | Battle pets (sold as caged pets) |

Use `--commodity` flag for the first column, omit it for the second.

If you're unsure, check Wowhead — the item page shows "Sell Price" or "Stack" size which indicates commodity behavior.

---

## Step 3 — Run the report

```powershell
cd C:\Users\petrd\wow-ah-sniper

# Non-commodity item (realm-specific, default Drak'Thul EU)
.\.venv\Scripts\python.exe item_report.py --item-id <ID> --name "<Item Name>"

# Commodity item (EU region-wide)
.\.venv\Scripts\python.exe item_report.py --item-id <ID> --name "<Item Name>" --commodity

# If you need JSON output for further processing (in addition to the HTML report)
.\.venv\Scripts\python.exe item_report.py --item-id <ID> --name "<Item Name>" [--commodity] --json
```

By default this produces THREE outputs next to `item_report.py`:
1. `item_<ID>_<scope>_<region>.html` — the **HTML dashboard report** (the main deliverable, see Step 4)
2. `item_<ID>_<scope>_<region>.png` — a static combo bar+line chart (for inline embedding in chat)
3. Formatted text printed to stdout (table with 14-day ranges)

Make sure the `.env` file in `C:\Users\petrd\wow-ah-sniper` contains `UNDERMINE_API_KEY`.
If it's missing, tell the user to add their key (see `.env.example` in that folder).

---

## Step 4 — Present the output

The **HTML dashboard report is the deliverable** the user wants. It's a self-contained,
dark-themed dashboard (styled like a modern analytics dashboard: stat pills up top, a
row of 3 small charts, a row of 3 larger charts each with mini stat cards underneath).
It uses Chart.js loaded from a CDN, so opening it later requires internet access.

**Always present, in this order:**
1. Tell the user the HTML report was generated and give its absolute path, e.g.:
   `C:\Users\petrd\wow-ah-sniper\item_<ID>_<scope>_<region>.html` — mention they can
   double-click it to open in their browser.
2. Embed the static PNG chart inline in chat as a quick visual preview (the chat UI can't
   render a live HTML file inline, only images):
   ```
   ![Price chart](C:\Users\petrd\wow-ah-sniper\item_<ID>_<realm>_eu.png)
   ```
3. Briefly summarize the text report's key numbers (current price, 24h range, 14d range)
   in your reply — don't just dump the raw table unless the user wants detail.

**HTML dashboard contains:**
- Header stat pills: current price, quantity on AH, 24h range, 14d range, and a
  **Recommendation pill** (Buy/Sell/Hold) — see below.
- **Recommendation pill**: compares the current price to a 30-day baseline average
  (from Undermine's all-time daily-history endpoint, `commodity_daily`/
  `item_daily_on_realm` — much longer range than the ~14-day hourly endpoint used
  for the rest of the report). Buy if price is ≥10% below the 30d average; Sell if
  price is high enough that, even after the Auction House's 5% cut on the sale, net
  proceeds are still ≥10% above the 30d average; otherwise Hold/"Fair price". Colored
  green (buy) / pink (sell) / neutral (hold). Omitted entirely if there's under 3 days
  of daily history (e.g. a brand-new item) — see `compute_baseline`/
  `compute_recommendation` in `item_report.py`.
- Top row (2 charts): 14-day daily min/max bar chart, and a **Weekday Buy/Sell
  Pattern** heatmap (30d) — two rows of 7 cells (Mon..Sun): the top row shows each
  weekday's average price vs. the 30-day window average (green = cheaper/buy-strong,
  pink = pricier/sell-strong), the bottom row shows each weekday's average AH
  quantity vs. the window average (blue intensity = more/less supply than usual).
  Cell intensity scales with the size of the deviation. Omitted (with a fallback
  message) if there's under a full week of daily history. See `compute_weekday_heatmap`
  in `item_report.py`.
- Bottom row (1 full-width combo chart): "Price & Volume Trend · 7d" — dual-axis chart with
  AH quantity as bars (left axis, blue) and price as a line (right axis, gold), plus two
  stat-card rows underneath (price stats: current/24h min/24h max; quantity stats:
  current/avg 7d/avg 14d)
- **Recipes section** (below the combo chart): every recipe that uses the searched item as
  a reagent, sorted by the crafted item's current AH price descending. Each row: crafted
  item icon + name (links to its Wowhead page), recipe name, yield (e.g. `×1` or `×2-3`),
  AH price, quantity on AH. Rows with no AH data (BoP/quest-only crafted items) sort last
  and show "no AH data". Sourced by scraping the searched item's Wowhead page for its
  "Reagent For" listview — see implementation notes below. Skip with `--no-recipes` if
  the user doesn't want it (e.g. for speed).
  - **If the item isn't used as a reagent in any known recipe**, the entire Recipes card
    (heading included) is omitted from the page — that area is simply left blank, rather
    than showing an empty-state message. This only applies when the Wowhead lookup
    *succeeds* and returns zero matches; if the lookup itself fails, the card still renders
    with a "Recipe data temporarily unavailable" note (see error handling below).
  - **Hovering a crafted item name** shows a tooltip **above** the row (not beneath it, so
    it never gets covered by the rows below) with the full materials breakdown: every
    reagent needed (including the searched item itself, highlighted gold with a ★),
    quantity needed, current AH price, and subtotal (price × qty). Below that: total
    Materials Cost, Crafted Value (crafted item's price × yield), and **Profit** = Crafted
    Value − Materials Cost, colored green if profitable / red (pink) if a loss. Shows "?"
    for any figure that couldn't be priced (no AH data on a reagent or the crafted item).

**Verifying the HTML renders correctly (do this after any change to the report template):**
If Microsoft Edge is available at `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`,
render it to a PNG and view that image yourself before telling the user it's ready:
```powershell
& "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --headless --disable-gpu `
  --screenshot="<tmp>.png" --window-size=1300,950 "file:///<absolute path to .html>"
```
Delete the temporary screenshot afterward — it's only for your own verification, not a
deliverable.

---

## Recipes section — implementation notes

`item_report.py` fetches the searched item's Wowhead page and parses its embedded
`reagent-for` listview JSON (recipes that consume it, including each recipe's full
`reagents` list) plus the page's item-metadata blob (names/icons of items referenced
elsewhere on the page). For crafted items/reagents missing from that blob, it falls back
to Wowhead's lightweight tooltip endpoint (`https://nether.wowhead.com/tooltip/item/<id>`)
to get the name/icon. Every item's AH price (crafted item + each reagent) is looked up via
the existing Undermine client (commodity first, realm fallback); the searched item's own
price is reused from the already-fetched header quote rather than re-queried. Both name/icon
lookups and price lookups are cached per item_id within one report run (`_cached_item_meta`,
`_cached_item_price`) since the same reagent often repeats across multiple recipes. Capped
at `MAX_RECIPE_ITEMS = 60` distinct crafted items per report.

**Important gotchas if you ever touch this code:**
- Wowhead sits behind bot-detection that blocks Python's `requests`/`urllib` outright
  (even with a spoofed User-Agent) but allows plain `curl` — so this shells out to `curl`
  rather than using `requests`. A **short, generic User-Agent** works; a full "realistic"
  modern Chrome UA string gets blocked (likely a UA/TLS-fingerprint mismatch heuristic).
- The bare URL `wowhead.com/item=<id>` (no slug) gets WAF-blocked. Always request
  `wowhead.com/item=<id>/x` (any placeholder slug) **with `curl -L`** so it follows
  Wowhead's 301 redirect to the canonical slugged URL.
- If Wowhead still fails/rate-limits after retries, `build_recipe_rows` raises and `main()`
  catches it, passing `recipe_rows=None` through so the report still generates — the
  Recipes section just shows "Recipe data temporarily unavailable" instead of crashing
  the whole report. Don't let a Wowhead hiccup block the rest of the deliverable.

---

## Answering common questions

| User asks | How to answer |
|---|---|
| "What's the price of X?" | Run the report, show current price and 24h range |
| "Is X a good deal right now?" | Compare current price to 14-day daily min; if current ≤ 14d low → good deal |
| "Price trend for X?" | Show the 14-day table and the chart; describe direction (rising/falling/stable) |
| "Should I buy/sell X?" | Current vs. 14d avg: buying below avg = good buy; selling above avg = good time to sell |
| "What's the cheapest X has been?" | Look at 14-day daily min column for the lowest value |

---

## Error handling

| Error | Action |
|---|---|
| `No Undermine API key found` | Ask user to add `UNDERMINE_API_KEY=<key>` to `wow-ah-sniper/.env` |
| `Undermine API request failed (404)` | Item ID may be wrong or item not tracked; verify on Wowhead |
| `Undermine API request failed (429)` | Rate limit hit (3,000 pts/hour); wait ~10 min and retry |
| Item shows `quantity: 0` | Item not currently listed on AH; show last known price and age |
| PNG chart not generated | Check matplotlib is installed: `pip3 install matplotlib` in the project dir |
| HTML report missing/blank charts | Check the `.html` file wasn't opened offline before Chart.js's CDN `<script>` loaded — needs internet access once |
