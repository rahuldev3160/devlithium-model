"""
devlithium-finance: log_expense.py
Logs an expense to finance.expense_log and deducts from pool fund balance.
Usage: python log_expense.py --category grocery --item "vegetables" --amount 350 --paid_by u1 --split equal
"""
import json, argparse, os
from datetime import date

KB_PATH = os.path.join(os.path.dirname(__file__), "../../../data/house_kb.json")

CATEGORIES = ["grocery", "cleaning", "repair", "utility", "maintenance", "other"]

def log_expense(category, item, amount, paid_by, split):
    if category not in CATEGORIES:
        print(f"⚠️ Unknown category '{category}'. Using 'other'.")
        category = "other"

    with open(KB_PATH) as f:
        kb = json.load(f)

    # Log expense
    expense = {
        "date": str(date.today()),
        "category": category,
        "item": item,
        "amount_inr": amount,
        "paid_by": paid_by,
        "split": split
    }
    kb["finance"]["expense_log"].append(expense)

    # Deduct from pool
    current = kb["finance"]["pool_fund"].get("current_balance", 0)
    new_balance = max(0, current - amount)
    kb["finance"]["pool_fund"]["current_balance"] = new_balance
    kb["_meta"]["last_updated"] = str(date.today())

    with open(KB_PATH, "w") as f:
        json.dump(kb, f, indent=2)

    minimum = kb["finance"]["pool_fund"].get("minimum_balance", 10000)
    alert = kb["finance"]["pool_fund"].get("alert_threshold", 12000)

    print(f"✅ Logged: {item} | ₹{amount} | Category: {category}")
    print(f"💰 New pool balance: ₹{new_balance:,.0f}")
    if new_balance < minimum:
        print(f"🔴 CRITICAL: Balance below minimum ₹{minimum:,.0f}! Top-up required.")
    elif new_balance < alert:
        print(f"🟡 WARNING: Balance below alert threshold ₹{alert:,.0f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--category", required=True)
    parser.add_argument("--item", required=True)
    parser.add_argument("--amount", type=float, required=True)
    parser.add_argument("--paid_by", default="u1")
    parser.add_argument("--split", default="equal")
    args = parser.parse_args()
    log_expense(args.category, args.item, args.amount, args.paid_by, args.split)
