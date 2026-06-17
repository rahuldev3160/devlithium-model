"""
devlithium-ventures: venture_coordinator.py
Evaluates, tracks, and coordinates business ventures for Devlithium residents.
Usage:
  python venture_coordinator.py --action log_idea --data '{"title":"Tiffin","proposed_by":"u2",...}'
  python venture_coordinator.py --action evaluate --venture_id v001
  python venture_coordinator.py --action skill_match --venture_id v001
  python venture_coordinator.py --action weekly_pulse --venture_id v001 --data '{"actual_revenue_inr":9500,"actual_expenses_inr":3200}'
  python venture_coordinator.py --action monthly_pl --venture_id v001
"""
import json
import argparse
import os
from datetime import date

PROFILES_DIR = os.path.join(os.path.dirname(__file__), "../../../data/profiles")
VENTURES_PATH = os.path.join(os.path.dirname(__file__), "../../../data/ventures.json")

USERS = ["u1", "u2", "u3"]
USER_NAMES = {"u1": "Dev", "u2": "Sunil", "u3": "Hanu"}


def load_profile(uid):
    path = os.path.join(PROFILES_DIR, f"{uid}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def load_ventures():
    if not os.path.exists(VENTURES_PATH):
        return {"ventures": [], "_meta": {"last_updated": str(date.today()), "total": 0}}
    with open(VENTURES_PATH) as f:
        return json.load(f)


def save_ventures(data):
    data["_meta"]["last_updated"] = str(date.today())
    data["_meta"]["total"] = len(data.get("ventures", []))
    with open(VENTURES_PATH, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def generate_venture_id(ventures_list):
    if not ventures_list:
        return "v001"
    existing_ids = [v.get("id", "v000") for v in ventures_list]
    nums = []
    for vid in existing_ids:
        try:
            nums.append(int(vid[1:]))
        except (ValueError, IndexError):
            nums.append(0)
    return f"v{max(nums) + 1:03d}"


def get_venture_by_id(venture_id):
    data = load_ventures()
    for v in data.get("ventures", []):
        if v.get("id") == venture_id:
            return data, v
    return data, None


def get_combined_capital():
    total = 0
    for uid in USERS:
        profile = load_profile(uid)
        if not profile:
            continue
        cap = profile.get("venture_interests", {}).get("capital_available_for_ventures_inr", 0) or 0
        total += cap
    return total


def get_all_skills():
    """Returns dict: skill -> list of {uid, name, expertise}"""
    skills_map = {}
    for uid in USERS:
        profile = load_profile(uid)
        if not profile:
            continue
        name = profile["_meta"]["name"]
        for skill_entry in profile.get("skills_and_expertise", []):
            # skill_entry can be a string or dict
            if isinstance(skill_entry, str):
                skill = skill_entry.lower()
                if skill not in skills_map:
                    skills_map[skill] = []
                skills_map[skill].append({"uid": uid, "name": name, "level": "known"})
            elif isinstance(skill_entry, dict):
                skill = skill_entry.get("skill", "").lower()
                if skill and skill not in skills_map:
                    skills_map[skill] = []
                if skill:
                    skills_map[skill].append({
                        "uid": uid,
                        "name": name,
                        "level": skill_entry.get("level", "known")
                    })
    return skills_map


def log_idea(raw_data_str):
    try:
        idea = json.loads(raw_data_str)
    except (json.JSONDecodeError, TypeError) as e:
        print(f"Error parsing --data JSON: {e}")
        return

    data = load_ventures()
    ventures = data.setdefault("ventures", [])
    vid = generate_venture_id(ventures)

    venture = {
        "id": vid,
        "title": idea.get("title", "Unnamed Venture"),
        "proposed_by": idea.get("proposed_by", "u1"),
        "date": str(date.today()),
        "stage": "idea",
        "description": idea.get("description", ""),
        "capital_required_inr": idea.get("capital_required_inr", 0),
        "expected_monthly_revenue_inr": idea.get("expected_monthly_revenue_inr", 0),
        "actual_revenue_inr": 0,
        "actual_expenses_inr": 0,
        "profit_inr": 0,
        "risk_level": idea.get("risk_level", "medium"),
        "participants": idea.get("participants", []),
        "skill_requirements": idea.get("skill_requirements", []),
        "monthly_loss_streak": 0,
        "notes": []
    }

    ventures.append(venture)
    save_ventures(data)

    # Quick auto-eval
    combined_cap = get_combined_capital()
    required = venture["capital_required_inr"]
    revenue = venture["expected_monthly_revenue_inr"]
    payback = round(required / revenue, 1) if revenue > 0 else float("inf")

    cap_ok = combined_cap >= required
    proposer_name = USER_NAMES.get(venture["proposed_by"], venture["proposed_by"])

    print(f"\nVENTURE LOGGED — {venture['title']} ({vid})")
    print("=" * 55)
    print(f"Proposed by:      {proposer_name}")
    print(f"Stage:            {venture['stage']}")
    print(f"Risk Level:       {venture['risk_level'].capitalize()}")
    print(f"Capital Required: INR {required:,.0f}")
    print(f"Combined Capital: INR {combined_cap:,.0f} — {'SUFFICIENT' if cap_ok else 'INSUFFICIENT'}")
    print(f"Expected Revenue: INR {revenue:,.0f}/month")
    if revenue > 0:
        print(f"Payback Period:   {payback} months")
    else:
        print(f"Payback Period:   Unknown (no revenue estimate)")

    if not cap_ok:
        shortfall = required - combined_cap
        print(f"\nWARNING: Shortfall of INR {shortfall:,.0f}. Need external funding or reduce scope.")

    print(f"\nRun evaluate to get full analysis: --action evaluate --venture_id {vid}")
    print()


def evaluate(venture_id):
    data, venture = get_venture_by_id(venture_id)
    if not venture:
        print(f"Venture {venture_id} not found in ventures.json")
        return

    print(f"\nVENTURE EVALUATION — {venture['title']} ({venture_id}) | {date.today()}")
    print("=" * 60)

    # 1. Capital Feasibility
    combined_cap = get_combined_capital()
    required = venture.get("capital_required_inr", 0)
    cap_ok = combined_cap >= required
    cap_status = "FEASIBLE" if cap_ok else f"SHORTFALL INR {required - combined_cap:,.0f}"

    print(f"\n1. CAPITAL FEASIBILITY")
    print(f"   Required:  INR {required:,.0f}")
    print(f"   Available: INR {combined_cap:,.0f}")
    print(f"   Status:    {cap_status}")

    # 2. Skill Coverage
    skills_map = get_all_skills()
    required_skills = venture.get("skill_requirements", [])
    covered = {}
    gaps = []

    print(f"\n2. SKILL COVERAGE")
    if not required_skills:
        print("   No skill requirements defined.")
    else:
        for req_skill in required_skills:
            req_lower = req_skill.lower()
            # Fuzzy match: check if any key starts with or contains the requirement
            match = None
            for key, holders in skills_map.items():
                if req_lower in key or key in req_lower:
                    match = holders
                    break
            if match:
                best = match[0]
                covered[req_skill] = best
                print(f"   {req_skill:<25} -> {best['name']} ({best['uid']}) [{best['level']}]")
            else:
                gaps.append(req_skill)
                print(f"   {req_skill:<25} -> GAP — External hire needed")

    # 3. ROI Model
    revenue = venture.get("expected_monthly_revenue_inr", 0)
    payback = round(required / revenue, 1) if revenue > 0 else None

    print(f"\n3. ROI MODEL")
    print(f"   Expected Monthly Revenue: INR {revenue:,.0f}")
    if required > 0 and revenue > 0:
        print(f"   Simple Payback:           {payback} months")
        annual_roi = round((revenue * 12 - required) / required * 100, 1) if required > 0 else 0
        print(f"   Year 1 ROI:               {annual_roi}%")
    else:
        print(f"   Payback:                  Cannot calculate — missing data")

    # 4. Risk Assessment
    risk = venture.get("risk_level", "medium")
    all_risks = []
    for uid in USERS:
        profile = load_profile(uid)
        if profile:
            all_risks.append(profile.get("financial", {}).get("risk_appetite", "moderate"))
    risk_rank = {"conservative": 1, "moderate": 2, "aggressive": 3}
    lowest_appetite = min(all_risks, key=lambda r: risk_rank.get(r, 2)) if all_risks else "moderate"

    risk_ok = risk_rank.get(risk, 2) <= risk_rank.get(lowest_appetite, 2)
    print(f"\n4. RISK ASSESSMENT")
    print(f"   Venture Risk:       {risk.capitalize()}")
    print(f"   Group Risk Limit:   {lowest_appetite.capitalize()}")
    print(f"   Compatibility:      {'OK' if risk_ok else 'MISMATCH — some residents may object'}")

    # 5. Recommendation
    print(f"\n5. RECOMMENDATION")
    if cap_ok and not gaps and risk_ok:
        rec = "GO — All conditions met. Recommend activating this venture."
        stage = "evaluated"
    elif cap_ok and not gaps:
        rec = "MODIFY — Capital and skills OK, but risk level may need discussion."
        stage = "evaluated"
    elif cap_ok:
        rec = f"MODIFY — Fill skill gaps first: {', '.join(gaps)}"
        stage = "evaluated"
    else:
        rec = "PASS for now — Insufficient capital. Revisit when funds grow."
        stage = "idea"

    print(f"   {rec}")

    # Update stage
    venture["stage"] = stage
    save_ventures(data)
    print(f"\n   Stage updated to: {stage}")
    print()


def skill_match(venture_id):
    data, venture = get_venture_by_id(venture_id)
    if not venture:
        print(f"Venture {venture_id} not found.")
        return

    skills_map = get_all_skills()
    required_skills = venture.get("skill_requirements", [])

    print(f"\nSKILL MATCH — {venture['title']} ({venture_id})")
    print("=" * 55)

    if not required_skills:
        print("No skill requirements defined for this venture.")
        return

    role_assignment = {}
    gaps = []

    for req_skill in required_skills:
        req_lower = req_skill.lower()
        match = None
        for key, holders in skills_map.items():
            if req_lower in key or key in req_lower:
                match = holders
                break
        if match:
            best = match[0]
            role_assignment.setdefault(best["uid"], []).append(req_skill)
            print(f"  {req_skill:<28} Covered by: {best['name']} ({best['uid']}) [{best['level']}]")
        else:
            gaps.append(req_skill)
            print(f"  {req_skill:<28} GAP — External hire needed")

    print(f"\nROLE ASSIGNMENT:")
    for uid, roles in role_assignment.items():
        name = USER_NAMES.get(uid, uid)
        print(f"  {name} ({uid}): {', '.join(roles)}")

    if gaps:
        print(f"\nGAPS (need hiring or training): {', '.join(gaps)}")
    else:
        print(f"\nAll roles covered internally — no external hire needed.")
    print()


def weekly_pulse(venture_id, raw_data_str):
    data, venture = get_venture_by_id(venture_id)
    if not venture:
        print(f"Venture {venture_id} not found.")
        return

    try:
        pulse = json.loads(raw_data_str)
    except (json.JSONDecodeError, TypeError) as e:
        print(f"Error parsing --data JSON: {e}")
        return

    revenue = pulse.get("actual_revenue_inr", venture.get("actual_revenue_inr", 0))
    expenses = pulse.get("actual_expenses_inr", venture.get("actual_expenses_inr", 0))
    profit = revenue - expenses

    venture["actual_revenue_inr"] = revenue
    venture["actual_expenses_inr"] = expenses
    venture["profit_inr"] = profit

    # Track monthly loss streak (approximated weekly)
    if profit < 0:
        venture["monthly_loss_streak"] = venture.get("monthly_loss_streak", 0) + 1
    else:
        venture["monthly_loss_streak"] = 0

    streak = venture.get("monthly_loss_streak", 0)

    note = {
        "date": str(date.today()),
        "type": "weekly_pulse",
        "revenue": revenue,
        "expenses": expenses,
        "profit": profit
    }
    venture.setdefault("notes", []).append(note)

    if venture.get("stage") == "idea":
        venture["stage"] = "active"

    save_ventures(data)

    print(f"\nWEEKLY PULSE — {venture['title']} ({venture_id}) | {date.today()}")
    print("=" * 50)
    print(f"Revenue:      INR {revenue:,.0f}")
    print(f"Expenses:     INR {expenses:,.0f}")
    print(f"Profit:       INR {profit:,.0f}")
    print(f"Loss Streak:  {streak} month-equivalent period(s)")

    if streak >= 3:
        print(f"\nAUTO-FLAG: 3+ consecutive loss periods detected.")
        print(f"RECOMMEND: Pause or close this venture. Awaiting u1 decision.")
        venture["stage"] = "paused"
        save_ventures(data)
    elif profit < 0:
        print(f"\nNote: This period shows a loss. Monitor closely.")
    else:
        print(f"\nStatus: Profitable this period.")
    print()


def monthly_pl(venture_id):
    data, venture = get_venture_by_id(venture_id)
    if not venture:
        print(f"Venture {venture_id} not found.")
        return

    revenue = venture.get("actual_revenue_inr", 0)
    expenses = venture.get("actual_expenses_inr", 0)
    profit = revenue - expenses
    capital = venture.get("capital_required_inr", 1)
    streak = venture.get("monthly_loss_streak", 0)

    roi_pct = round((profit / capital) * 100, 1) if capital > 0 else 0.0

    if profit > 0:
        pl_status = "Profitable"
        action = "Continue — venture is healthy."
    elif profit == 0:
        pl_status = "Break-even"
        action = "Review — optimize expenses or increase revenue."
    else:
        pl_status = f"Loss (streak: {streak} period(s))"
        action = "PAUSE RECOMMENDED" if streak >= 3 else "Monitor closely next period."

    from datetime import datetime
    month_label = datetime.today().strftime("%B %Y")

    print(f"\nMONTHLY P&L — {venture['title']} ({venture_id}) | {month_label}")
    print("=" * 55)
    print(f"Revenue:      INR {revenue:,.0f}")
    print(f"Expenses:     INR {expenses:,.0f}")
    print(f"Profit:       INR {profit:,.0f}")
    print(f"ROI:          {roi_pct}% on capital INR {capital:,.0f}")
    print(f"Status:       {pl_status}")
    print(f"Action:       {action}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Devlithium Venture Coordinator")
    parser.add_argument(
        "--action",
        required=True,
        choices=["log_idea", "evaluate", "skill_match", "weekly_pulse", "monthly_pl"],
        help="Action to perform"
    )
    parser.add_argument(
        "--venture_id",
        default=None,
        help="Venture ID e.g. v001"
    )
    parser.add_argument(
        "--data",
        default=None,
        help="JSON string with venture data or pulse data"
    )
    args = parser.parse_args()

    if args.action == "log_idea":
        if not args.data:
            print("--data is required for log_idea")
            return
        log_idea(args.data)

    elif args.action == "evaluate":
        if not args.venture_id:
            print("--venture_id is required for evaluate")
            return
        evaluate(args.venture_id)

    elif args.action == "skill_match":
        if not args.venture_id:
            print("--venture_id is required for skill_match")
            return
        skill_match(args.venture_id)

    elif args.action == "weekly_pulse":
        if not args.venture_id or not args.data:
            print("--venture_id and --data are required for weekly_pulse")
            return
        weekly_pulse(args.venture_id, args.data)

    elif args.action == "monthly_pl":
        if not args.venture_id:
            print("--venture_id is required for monthly_pl")
            return
        monthly_pl(args.venture_id)


if __name__ == "__main__":
    main()
