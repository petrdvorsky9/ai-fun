#!/usr/bin/env python3
"""
Alpro Milk Price Checker — Czech Grocery Stores
Uses the Potravinka.cz public API (no auth required).
Covered stores: LIDL, Kaufland, Albert, BILLA, Penny, Tesco,
                Globus, Makro, rohlik.cz, Kosik.cz, COOP
"""

import sys
import argparse
import requests
from collections import defaultdict

API_BASE = "https://potravinka.cz"
SEARCH_URL = f"{API_BASE}/api/search/smart"

# Store display order (most recognisable brick-and-mortar first)
STORE_ORDER = [
    "LIDL", "Kaufland", "Albert", "BILLA", "Penny",
    "Tesco", "Globus", "Makro", "rohlik.cz", "Kosik.cz", "COOP",
]

# Keywords that identify plant-based milk/drink products
MILK_KEYWORDS = [
    "nápoj", "napoj", "milk", "drink", "sójový", "sojovy",
    "ovesný", "ovesny", "mandl", "rýžov", "ryzov",
    "kokosov", "barista", "oat", "soy", "almond", "rice",
]

# Product types the user can filter with --type
TYPE_ALIASES = {
    "soy":     ["sój", "sojov", "soy"],
    "oat":     ["oves", "oat"],
    "almond":  ["mandl", "almond"],
    "rice":    ["rýž", "rice", "ryz"],
    "coconut": ["kokos", "coconut"],
    "barista": ["barista"],
}


def fetch_alpro_products(query: str = "alpro", limit: int = 100) -> list[dict]:
    """Fetch Alpro products from the Potravinka API."""
    try:
        resp = requests.get(
            SEARCH_URL,
            params={"q": query, "limit": limit},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json().get("products", [])
    except requests.exceptions.Timeout:
        print("Error: request to potravinka.cz timed out.", file=sys.stderr)
        sys.exit(1)
    except requests.exceptions.RequestException as exc:
        print(f"Error fetching data: {exc}", file=sys.stderr)
        sys.exit(1)


def is_milk_product(name: str) -> bool:
    """Return True if the product name looks like a plant-based drink/milk."""
    name_lower = name.lower()
    return any(kw in name_lower for kw in MILK_KEYWORDS)


def matches_type_filter(name: str, type_filter: str) -> bool:
    """Return True if the product name matches the requested milk type."""
    keywords = TYPE_ALIASES.get(type_filter.lower(), [type_filter.lower()])
    name_lower = name.lower()
    return any(kw in name_lower for kw in keywords)


def format_price(price: float) -> str:
    return f"{price:.0f} Kč" if price == int(price) else f"{price:.2f} Kč"


def print_results(products: list[dict], show_all: bool, type_filter: str | None) -> None:
    """Print products grouped by store, sorted by price."""
    # Optional filtering
    if not show_all:
        products = [p for p in products if is_milk_product(p["name"])]
    if type_filter:
        products = [p for p in products if matches_type_filter(p["name"], type_filter)]

    if not products:
        print("No matching Alpro products found.")
        return

    # Group by store
    by_store: dict[str, list[dict]] = defaultdict(list)
    for p in products:
        by_store[p["store"]].append(p)

    # Sort each store's products by price
    for store in by_store:
        by_store[store].sort(key=lambda p: p["price"])

    # Print in preferred store order, then any remaining alphabetically
    ordered_stores = [s for s in STORE_ORDER if s in by_store]
    ordered_stores += sorted(s for s in by_store if s not in STORE_ORDER)

    total = sum(len(v) for v in by_store.values())
    print(f"\nFound {total} Alpro product(s) across {len(by_store)} store(s):\n")
    print("=" * 65)

    for store in ordered_stores:
        items = by_store[store]
        print(f"\n{store}  ({len(items)} product{'s' if len(items) != 1 else ''})")
        print("-" * 65)
        for p in items:
            amount = f"  [{p['amount']}]" if p.get("amount") else ""
            stock_tag = "" if p.get("stock", 1) else "  [out of stock]"
            print(f"  {format_price(p['price']):>10}  {p['name']}{amount}{stock_tag}")

    print("\n" + "=" * 65)
    print("Prices in CZK incl. VAT — data from potravinka.cz\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Search Czech grocery stores for Alpro milk prices.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python alpro_prices.py                  # all Alpro milk/drink products
  python alpro_prices.py --all            # include yogurts, creams, etc.
  python alpro_prices.py --type soy       # soy drinks only
  python alpro_prices.py --type oat       # oat drinks only
  python alpro_prices.py --type almond    # almond drinks only
  python alpro_prices.py --type barista   # barista editions only
  python alpro_prices.py --query "alpro barista"  # custom search term
  python alpro_prices.py --limit 200      # fetch more results

Milk type shortcuts: soy, oat, almond, rice, coconut, barista
        """,
    )
    parser.add_argument(
        "--query", "-q",
        default="alpro",
        help="Search query (default: 'alpro')",
    )
    parser.add_argument(
        "--type", "-t",
        dest="milk_type",
        metavar="TYPE",
        help="Filter by milk type: soy, oat, almond, rice, coconut, barista",
    )
    parser.add_argument(
        "--all", "-a",
        action="store_true",
        help="Show all Alpro products, not just milk/drink variants",
    )
    parser.add_argument(
        "--limit", "-l",
        type=int,
        default=100,
        help="Max results to fetch from API (default: 100, max: 100)",
    )
    args = parser.parse_args()

    print(f"Searching for Alpro products across Czech grocery stores…")
    products = fetch_alpro_products(query=args.query, limit=args.limit)
    print_results(products, show_all=args.all, type_filter=args.milk_type)


if __name__ == "__main__":
    main()
