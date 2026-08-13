"""WoW AH Item Report — Drak'Thul EU (Undermine Exchange)

Generates a price analysis for a given item:
  • Current price, quantity, and data freshness
  • 24-hour price range (min / max)
  • 14-day daily price ranges (min and max per day, derived from hourly data)
  • Combo chart: hourly price line + volume bars for the last 7 days

Usage:
    # Non-commodity item (gear, mounts, pets — realm-specific)
    python item_report.py --item-id 118852 --name "Invincible's Reins"

    # Commodity item (ore, herbs, cloth, enchanting mats — EU region-wide)
    python item_report.py --item-id 251285 --name "Petrified Root" --commodity

    # Save chart to a specific path
    python item_report.py --item-id 251285 --name "Petrified Root" --commodity --out /tmp/chart.png

    # Print JSON for programmatic use
    python item_report.py --item-id 251285 --commodity --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path

import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

from undermine_client import (
    DailySnapshot,
    PriceSnapshot,
    UndermineApiError,
    UndermineClient,
)

# ── defaults ──────────────────────────────────────────────────────────────────
DEFAULT_REALM = "drakthul"
DEFAULT_REGION = "eu"
CHART_DAYS = 7
DAILY_HISTORY_DAYS = 14

# ── copper helpers ─────────────────────────────────────────────────────────────

def copper_to_gold(copper: int) -> float:
    return copper / 10_000


def fmt_gold(copper: int) -> str:
    g = copper // 10_000
    s = (copper % 10_000) // 100
    c = copper % 100
    return f"{g:,}g {s:02d}s {c:02d}c"


# ── statistics ─────────────────────────────────────────────────────────────────

def parse_dt(iso: str) -> datetime:
    return datetime.fromisoformat(iso.replace("Z", "+00:00"))


def last_n_hours(snapshots: list[PriceSnapshot], hours: int) -> list[PriceSnapshot]:
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    return [s for s in snapshots if parse_dt(s.snapshot) >= cutoff]


def last_n_days(snapshots: list[PriceSnapshot], days: int) -> list[PriceSnapshot]:
    return last_n_hours(snapshots, days * 24)


def daily_ranges(snapshots: list[PriceSnapshot]) -> dict[str, dict]:
    """Group hourly snapshots by UTC date and compute min/max/avg price per day."""
    by_day: dict[str, list[int]] = defaultdict(list)
    qty_by_day: dict[str, list[int]] = defaultdict(list)
    for s in snapshots:
        if s.price_copper <= 0:
            continue
        day = parse_dt(s.snapshot).strftime("%Y-%m-%d")
        by_day[day].append(s.price_copper)
        qty_by_day[day].append(s.quantity)
    result = {}
    for day in sorted(by_day):
        prices = by_day[day]
        result[day] = {
            "min": min(prices),
            "max": max(prices),
            "avg": sum(prices) / len(prices),
            "avg_qty": int(sum(qty_by_day[day]) / len(qty_by_day[day])),
        }
    return result


# ── chart ──────────────────────────────────────────────────────────────────────

def _gold_formatter(value: float, _pos: int) -> str:
    """Format y-axis tick labels as e.g. '1,234g'."""
    return f"{int(value):,}g"


def render_chart(
    snapshots_7d: list[PriceSnapshot],
    item_name: str,
    item_id: int,
    out_path: Path,
    scope: str,
    region: str,
) -> None:
    """Render a combo bar+line chart: volume bars + price line, last 7 days."""
    valid = [s for s in snapshots_7d if s.price_copper > 0]
    if not valid:
        print("[chart] No data with price > 0 in the last 7 days — chart skipped.", file=sys.stderr)
        return

    x = [parse_dt(s.snapshot) for s in valid]
    prices_gold = [copper_to_gold(s.price_copper) for s in valid]
    quantities = [s.quantity for s in valid]

    fig, ax_vol = plt.subplots(figsize=(14, 5))
    ax_price = ax_vol.twinx()

    fig.patch.set_facecolor("#1a1a2e")
    for ax in (ax_vol, ax_price):
        ax.set_facecolor("#16213e")
        ax.tick_params(colors="#c8cdd6")
        ax.spines[:].set_color("#2a2a4a")

    # Volume bars (primary axis, left)
    bar_color = "#3a7bd5"
    bar_width = timedelta(minutes=40)
    ax_vol.bar(x, quantities, width=bar_width, color=bar_color, alpha=0.45, label="Volume")
    ax_vol.set_ylabel("Quantity on AH", color=bar_color, fontsize=10)
    ax_vol.tick_params(axis="y", labelcolor=bar_color)
    ax_vol.yaxis.set_major_formatter(mticker.FuncFormatter(lambda v, _: f"{int(v):,}"))

    # Price line (secondary axis, right)
    line_color = "#f0c040"
    ax_price.plot(x, prices_gold, color=line_color, linewidth=1.6, label="Price", zorder=3)
    ax_price.set_ylabel("Price (gold)", color=line_color, fontsize=10)
    ax_price.tick_params(axis="y", labelcolor=line_color)
    ax_price.yaxis.set_major_formatter(mticker.FuncFormatter(_gold_formatter))

    # X-axis formatting
    ax_vol.xaxis.set_major_locator(mdates.DayLocator(interval=1, tz=timezone.utc))
    ax_vol.xaxis.set_major_formatter(mdates.DateFormatter("%b %d", tz=timezone.utc))
    ax_vol.xaxis.set_minor_locator(mdates.HourLocator(byhour=range(0, 24, 6), tz=timezone.utc))
    plt.setp(ax_vol.xaxis.get_majorticklabels(), rotation=30, ha="right", color="#c8cdd6")

    scope_label = "EU Region (Commodity)" if scope == "region" else f"{scope.title()} / {region.upper()}"
    ax_vol.set_title(
        f"{item_name}  (item {item_id})  ·  {scope_label}  ·  Last 7 days",
        color="#e0e0f0",
        fontsize=12,
        pad=12,
    )

    # Combined legend
    lines_vol, labels_vol = ax_vol.get_legend_handles_labels()
    lines_price, labels_price = ax_price.get_legend_handles_labels()
    ax_price.legend(
        lines_vol + lines_price,
        labels_vol + labels_price,
        loc="upper left",
        facecolor="#1a1a2e",
        edgecolor="#2a2a4a",
        labelcolor="#c8cdd6",
        fontsize=9,
    )

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=140, facecolor=fig.get_facecolor())
    plt.close(fig)


# ── text report ────────────────────────────────────────────────────────────────

_BAR_CHARS = " ▁▂▃▄▅▆▇█"

def _sparkbar(value: int, max_value: int, width: int = 8) -> str:
    if max_value == 0:
        return _BAR_CHARS[0] * width
    ratio = value / max_value
    filled = round(ratio * width)
    idx = min(len(_BAR_CHARS) - 1, max(1, round(ratio * (len(_BAR_CHARS) - 1))))
    return _BAR_CHARS[idx] * filled + " " * (width - filled)


def print_report(
    item_name: str,
    item_id: int,
    commodity: bool,
    realm: str,
    region: str,
    current_price: int,
    current_qty: int,
    last_updated: str | None,
    snapshots_all: list[PriceSnapshot],
    chart_path: Path | None,
) -> None:
    now_utc = datetime.now(timezone.utc)
    scope = "EU Region (Commodity)" if commodity else f"{realm.title()} / {region.upper()}"

    # 24h range
    h24 = [s for s in last_n_hours(snapshots_all, 24) if s.price_copper > 0]
    h24_min = min((s.price_copper for s in h24), default=current_price)
    h24_max = max((s.price_copper for s in h24), default=current_price)

    # 14-day daily ranges (from hourly data)
    hist_14d = last_n_days(snapshots_all, DAILY_HISTORY_DAYS)
    ranges = daily_ranges(hist_14d)
    last_14 = sorted(ranges.items())[-DAILY_HISTORY_DAYS:]

    # max price across 14d for sparkline scaling
    max_14d = max((v["max"] for _, v in last_14), default=current_price) or 1

    W = 64
    sep = "─" * W

    updated_str = ""
    if last_updated:
        try:
            age = now_utc - parse_dt(last_updated)
            mins = int(age.total_seconds() // 60)
            updated_str = f"  updated {mins}m ago"
        except Exception:
            updated_str = f"  updated {last_updated}"

    print(f"\n{'═' * W}")
    print(f"  {item_name}  │  item {item_id}  │  {scope}{updated_str}")
    print(f"{'═' * W}")
    print(f"  Current price   {fmt_gold(current_price):<24}  ×{current_qty:,} on AH")
    print(f"  24h range       {fmt_gold(h24_min)}  –  {fmt_gold(h24_max)}")
    print(f"{sep}")
    print(f"  14-day daily price ranges  (hourly min – max)")
    print(f"  {'Date':<12}  {'Min':>14}  {'Max':>14}  {'Avg qty':>9}  Chart")

    for day, stats in last_14:
        bar_min = _sparkbar(stats["min"], max_14d, 6)
        bar_max = _sparkbar(stats["max"], max_14d, 6)
        try:
            dt = datetime.strptime(day, "%Y-%m-%d")
            day_label = dt.strftime("%a %b %d")
        except ValueError:
            day_label = day
        print(
            f"  {day_label:<12}  "
            f"{fmt_gold(stats['min']):>14}  "
            f"{fmt_gold(stats['max']):>14}  "
            f"{stats['avg_qty']:>9,}  "
            f"{bar_min}…{bar_max}"
        )

    print(f"{sep}")
    if chart_path and chart_path.exists():
        print(f"  Chart saved → {chart_path}")
    print(f"{'═' * W}\n")


# ── JSON output ─────────────────────────────────────────────────────────────────

def build_json(
    item_name: str,
    item_id: int,
    commodity: bool,
    realm: str,
    region: str,
    current_price: int,
    current_qty: int,
    last_updated: str | None,
    snapshots_all: list[PriceSnapshot],
    chart_path: Path | None,
) -> dict:
    h24 = [s for s in last_n_hours(snapshots_all, 24) if s.price_copper > 0]
    hist_14d = last_n_days(snapshots_all, DAILY_HISTORY_DAYS)
    ranges = daily_ranges(hist_14d)
    last_14 = {day: v for day, v in sorted(ranges.items())[-DAILY_HISTORY_DAYS:]}
    return {
        "item_id": item_id,
        "item_name": item_name,
        "commodity": commodity,
        "realm": realm if not commodity else None,
        "region": region,
        "current_price_copper": current_price,
        "current_price_gold": fmt_gold(current_price),
        "current_quantity": current_qty,
        "last_updated": last_updated,
        "h24_min_copper": min((s.price_copper for s in h24), default=current_price),
        "h24_max_copper": max((s.price_copper for s in h24), default=current_price),
        "daily_14d": {
            day: {
                "min_copper": v["min"],
                "max_copper": v["max"],
                "avg_copper": int(v["avg"]),
                "avg_qty": v["avg_qty"],
            }
            for day, v in last_14.items()
        },
        "chart_path": str(chart_path) if chart_path and chart_path.exists() else None,
    }


# ── main ───────────────────────────────────────────────────────────────────────

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="WoW AH item price report — Drak'Thul EU (Undermine Exchange)"
    )
    p.add_argument("--item-id", type=int, required=True, help="WoW item ID")
    p.add_argument("--name", default="", help="Item display name (cosmetic)")
    p.add_argument(
        "--commodity",
        action="store_true",
        help="Treat as a stackable commodity (EU region-wide AH)",
    )
    p.add_argument(
        "--realm",
        default=DEFAULT_REALM,
        help=f"Realm slug (default: {DEFAULT_REALM}; only used for non-commodities)",
    )
    p.add_argument(
        "--region",
        default=DEFAULT_REGION,
        choices=["us", "eu", "tw", "kr"],
        help=f"Region (default: {DEFAULT_REGION})",
    )
    p.add_argument(
        "--out",
        default="",
        help="Chart output path (default: item_<id>_<realm>.png next to this script)",
    )
    p.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Print machine-readable JSON instead of the formatted report",
    )
    p.add_argument(
        "--no-chart",
        action="store_true",
        help="Skip chart generation",
    )
    return p


def main() -> None:
    args = build_parser().parse_args()

    item_id: int = args.item_id
    item_name: str = args.name or f"Item {item_id}"
    commodity: bool = args.commodity
    realm: str = args.realm
    region: str = args.region

    # Chart output path
    if args.no_chart:
        chart_path: Path | None = None
    elif args.out:
        chart_path = Path(args.out)
    else:
        scope_slug = "commodity" if commodity else realm
        chart_path = Path(__file__).parent / f"item_{item_id}_{scope_slug}_{region}.png"

    try:
        client = UndermineClient()

        # Fetch current price
        if commodity:
            now_quote = client.commodity_now(region, item_id)
        else:
            now_quote = client.item_now_on_realm(region, realm, item_id)

        # Fetch hourly history (~14 days)
        if commodity:
            hourly: list[PriceSnapshot] = client.commodity_hourly(region, item_id)
        else:
            hourly = client.item_hourly_on_realm(region, realm, item_id)

    except UndermineApiError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)

    # Slice last 7 days for the chart
    snapshots_7d = last_n_days(hourly, CHART_DAYS)

    # Render chart
    if chart_path is not None:
        scope = "region" if commodity else realm
        render_chart(snapshots_7d, item_name, item_id, chart_path, scope, region)

    # Output
    if args.as_json:
        print(json.dumps(
            build_json(
                item_name, item_id, commodity, realm, region,
                now_quote.price_copper, now_quote.quantity,
                now_quote.last_updated, hourly, chart_path,
            ),
            indent=2,
        ))
    else:
        print_report(
            item_name, item_id, commodity, realm, region,
            now_quote.price_copper, now_quote.quantity,
            now_quote.last_updated, hourly, chart_path,
        )


if __name__ == "__main__":
    main()
