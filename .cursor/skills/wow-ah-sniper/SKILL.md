# WoW AH Sniper — Item Query Skill

## Purpose
Standardized way to answer any question about a World of Warcraft auction house item's price, history, or market trends.

## Fixed defaults — always use these unless the user explicitly overrides
| Setting | Value |
|---|---|
| Realm | `drakthul` (Drak'Thul EU) |
| Region | `eu` |
| Data source | Undermine Exchange (main) |
| Script | `wow-ah-sniper/item_report.py` |

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

```bash
cd /workspace/wow-ah-sniper

# Non-commodity item (realm-specific, default Drak'Thul EU)
python3 item_report.py --item-id <ID> --name "<Item Name>"

# Commodity item (EU region-wide)
python3 item_report.py --item-id <ID> --name "<Item Name>" --commodity

# If you need JSON output for further processing
python3 item_report.py --item-id <ID> --name "<Item Name>" [--commodity] --json
```

Make sure the `.env` file in `wow-ah-sniper/` contains `UNDERMINE_API_KEY`.
If it's missing, tell the user to add their key (see `wow-ah-sniper/.env.example`).

---

## Step 4 — Present the output

The script prints a formatted text report AND saves a chart image.

**Always present:**
1. The full text report output (copy it verbatim — it contains the table and 14-day ranges)
2. The chart image using an inline image reference, e.g.:
   ```
   ![Price chart](wow-ah-sniper/item_<ID>_<realm>_eu.png)
   ```

**Report contains:**
- Current price (gold/silver/copper) and quantity currently listed on AH
- 24-hour price range (min – max of all hourly snapshots in the last 24h)
- 14-day daily price ranges (hourly min and max per calendar day)
- Chart path

**Chart contains (combo bar+line, last 7 days):**
- Left Y-axis: quantity/volume (blue semi-transparent bars)
- Right Y-axis: price in gold (gold-colored line)
- X-axis: hourly snapshots with daily labels

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
| Chart not generated | Check matplotlib is installed: `pip3 install matplotlib` in the project dir |
