"""
devlithium-finance: fund_check.py
Checks pool fund balance and projects 7-day spend.
"""
import json, os
from datetime import date

KB_PATH = os.path.join(os.path.dirname(__file__), "../../../data/house_kb.json")

def check():
    with open(KB_PATH) as f:
        kb = json.load(f)
    pf = kb["finance"]["pool_fund"]
    balance = pf.get("current_balance", 0)
    minimum = pf.get("minimum_balance", 10000)
    alert = pf.get("alert_threshold", 12000)

    # Project 7-day spend from monthly fixed costs
    fixed = kb["finance"].get("monthly_fixed_costs", {})
    monthly_fixed = sum(v for v in fixed.values() if isinstance(v, (int, float)))
    weekly_fixed = monthly_fixed / 4
    # Estimate weekly grocery from inventory consumption
    grocery_weekly = sum(
        (item.get("weekly_consumption", 0) or 0) * 50  # rough ₹50/unit avg
        for item in kb["inventory"].get("grocery", [])
    )
    projected_7day = weekly_fixed + grocery_weekly
    projected_balance = balance - projected_7day

    # Status
    if balance < minimum:
        status = "🔴 CRITICAL"
    elif balance < alert:
        status = "🟡 WARNING"
    else:
        status = "🟢 OK"

    n_residents = len([r for r in kb.get("residents", []) if r.get("role") != "inactive"])
    topup_each = max(0, (15000 - balance) / max(n_residents, 1))

    print(f"\n💰 POOL FUND STATUS — {date.today()}")
    print(f"{'='*40}")
    print(f"Current balance:       ₹{balance:,.0f}")
    print(f"Status:                {status}")
    print(f"Projected 7-day spend: ₹{projected_7day:,.0f}")
    print(f"Projected balance:     ₹{projected_balance:,.0f}")
    if balance < alert:
        print(f"\n⚡ Top-up needed: ₹{topup_each:,.0f} per person (to reach ₹15,000 safe buffer)")
    print()

if __name__ == "__main__":
    check()
