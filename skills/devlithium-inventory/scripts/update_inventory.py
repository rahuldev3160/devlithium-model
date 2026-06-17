"""
devlithium-inventory: update_inventory.py
Updates qty for an item and logs the purchase to finance.expense_log.
Usage: python update_inventory.py --item "Milk" --qty 3 --unit liters --cost 150 --buyer u1
"""
import json, argparse, os
from datetime import date

KB_PATH = os.path.join(os.path.dirname(__file__), "../../../data/house_kb.json")

def update(item_name, qty, unit, cost, buyer):
    with open(KB_PATH) as f:
        kb = json.load(f)

    # Find and update item
    updated = False
    for section in ["grocery", "cleaning_supplies"]:
        for item in kb["inventory"].get(section, []):
            if item["item"].lower() == item_name.lower():
                item["current_qty"] = (item.get("current_qty") or 0) + qty
                updated = True
                print(f"✅ Updated {item_name}: new qty = {item['current_qty']} {unit}")
                break
        if updated:
            break

    if not updated:
        print(f"⚠️  Item '{item_name}' not found in inventory. Add it via setup skill first.")
        return

    # Log to finance
    expense = {
        "date": str(date.today()),
        "category": "grocery",
        "item": item_name,
        "qty": qty,
        "unit": unit,
        "amount_inr": cost,
        "paid_by": buyer,
        "split": "equal"
    }
    kb["finance"]["expense_log"].append(expense)

    # Update pool balance
    kb["finance"]["pool_fund"]["current_balance"] = max(
        0, kb["finance"]["pool_fund"].get("current_balance", 0) - cost
    )

    # Write back
    kb["_meta"]["last_updated"] = str(date.today())
    with open(KB_PATH, "w") as f:
        json.dump(kb, f, indent=2)

    balance = kb["finance"]["pool_fund"]["current_balance"]
    print(f"💰 ₹{cost} logged | Pool balance: ₹{balance}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--item", required=True)
    parser.add_argument("--qty", type=float, required=True)
    parser.add_argument("--unit", default="units")
    parser.add_argument("--cost", type=float, default=0)
    parser.add_argument("--buyer", default="u1")
    args = parser.parse_args()
    update(args.item, args.qty, args.unit, args.cost, args.buyer)
