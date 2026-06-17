"""
devlithium-inventory: check_inventory.py
Reads house_kb.json and prints inventory status with reorder flags.
"""
import json, os
from datetime import date

KB_PATH = os.path.join(os.path.dirname(__file__), "../../../data/house_kb.json")

def check():
    with open(KB_PATH) as f:
        kb = json.load(f)

    all_items = kb["inventory"].get("grocery", []) + kb["inventory"].get("cleaning_supplies", [])
    critical, low, ok = [], [], []

    for item in all_items:
        qty = item.get("current_qty", 0)
        threshold = item.get("reorder_threshold", 1)
        if qty == 0:
            critical.append(item)
        elif qty <= threshold:
            low.append(item)
        else:
            ok.append(item)

    print(f"\n🛒 INVENTORY STATUS — {date.today()}")
    print(f"{'='*40}")
    if critical:
        print(f"🔴 CRITICAL (qty=0): {', '.join(i['item'] for i in critical)}")
    if low:
        low_strs = ["{} ({} {})".format(i['item'], i['current_qty'], i['unit']) for i in low]
        print(f"🟡 LOW: {', '.join(low_strs)}")
    print(f"🟢 OK: {len(ok)} items")

    # Suggested order
    to_order = critical + low
    if to_order:
        print(f"\n📋 Suggested order:")
        for item in to_order:
            need = (item.get("weekly_consumption", 1) or 1) - item.get("current_qty", 0)
            print(f"  • {item['item']}: {max(need, 1)} {item['unit']} — via {item.get('supplier', 'any')}")
    else:
        print("\n✅ All items stocked. No reorder needed.")
    print()

if __name__ == "__main__":
    check()
