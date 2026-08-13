"""WoW Auction House sniper, powered by the Undermine Exchange API.

Usage:
    # One-off price check
    python sniper.py check --item-id 251285 --region eu --commodity

    python sniper.py check --item-id 251285 --region eu --realm drakthul

    # Watch everything in watchlist.yaml and alert on deals, polling every
    # 5 minutes (Undermine data itself refreshes roughly hourly, matching
    # Blizzard's AH snapshot cadence, so polling much faster rarely helps).
    python sniper.py watch --interval 300
"""

from __future__ import annotations

import argparse
import sys
import time
from datetime import datetime
from pathlib import Path

import yaml

from undermine_client import PriceQuote, UndermineApiError, UndermineClient

WATCHLIST_PATH = Path(__file__).parent / "watchlist.yaml"


def load_watchlist(path: Path = WATCHLIST_PATH) -> list[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Watchlist not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data.get("items", [])


def fetch_quote(client: UndermineClient, entry: dict) -> PriceQuote:
    region = entry["region"]
    item_id = entry["item_id"]
    if entry.get("commodity"):
        return client.commodity_now(region, item_id)
    realm = entry.get("realm")
    if not realm:
        raise ValueError(f"Item {entry.get('name', item_id)} needs a 'realm' (commodity: false)")
    return client.item_now_on_realm(region, realm, item_id)


def print_quote(name: str, quote: PriceQuote, max_price_gold: float | None = None) -> bool:
    is_deal = max_price_gold is not None and quote.gold <= max_price_gold
    marker = " <<< DEAL!" if is_deal else ""
    print(
        f"[{datetime.now().strftime('%H:%M:%S')}] "
        f"{name} ({quote.scope}/{quote.region}): "
        f"{quote.formatted()}  x{quote.quantity}{marker}"
    )
    return is_deal


def cmd_check(args: argparse.Namespace) -> None:
    client = UndermineClient()
    entry = {
        "item_id": args.item_id,
        "region": args.region,
        "commodity": args.commodity,
        "realm": args.realm,
    }
    try:
        quote = fetch_quote(client, entry)
    except UndermineApiError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        sys.exit(1)
    print_quote(f"item {args.item_id}", quote)


def cmd_watch(args: argparse.Namespace) -> None:
    client = UndermineClient()
    watchlist = load_watchlist(Path(args.watchlist))
    if not watchlist:
        print("Watchlist is empty. Add items to watchlist.yaml first.", file=sys.stderr)
        sys.exit(1)

    print(f"Watching {len(watchlist)} item(s), polling every {args.interval}s. Ctrl+C to stop.\n")
    try:
        while True:
            for entry in watchlist:
                name = entry.get("name", str(entry["item_id"]))
                try:
                    quote = fetch_quote(client, entry)
                except UndermineApiError as exc:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] {name}: ERROR - {exc}")
                    continue
                is_deal = print_quote(name, quote, entry.get("max_price_gold"))
                if is_deal:
                    print("\a", end="")  # terminal bell
            print("-" * 60)
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nStopped.")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WoW Auction House sniper (Undermine Exchange API)")
    sub = parser.add_subparsers(dest="command", required=True)

    check = sub.add_parser("check", help="One-off price lookup for a single item")
    check.add_argument("--item-id", type=int, required=True, help="WoW item ID")
    check.add_argument("--region", required=True, choices=["us", "eu", "tw", "kr"])
    check.add_argument("--commodity", action="store_true", help="Item is a stackable commodity")
    check.add_argument("--realm", help="Realm slug (required if not --commodity)")
    check.set_defaults(func=cmd_check)

    watch = sub.add_parser("watch", help="Poll watchlist.yaml on a loop and alert on deals")
    watch.add_argument("--interval", type=int, default=300, help="Seconds between polls (default 300)")
    watch.add_argument("--watchlist", default=str(WATCHLIST_PATH), help="Path to watchlist YAML")
    watch.set_defaults(func=cmd_watch)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
