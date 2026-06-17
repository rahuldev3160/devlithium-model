"""
devlithium-repair: repair_manager.py
Manages the full lifecycle of home repair issues.
Usage:
  --action log       --description "..." --room r1 --priority high
  --action quote     --id REP-001 --provider "Urban Company" --cost 850
  --action approve   --id REP-001 --approved_by u1 --provider "Urban Company" --cost 850
  --action schedule  --id REP-001 --scheduled_date 2026-05-16
  --action resolve   --id REP-001 --cost 850
  --action status    --id REP-001
  --action list
"""
import json
import argparse
import os
import subprocess
import sys
from datetime import date, datetime

KB_PATH = os.path.join(os.path.dirname(__file__), "../../../data/house_kb.json")
FINANCE_SCRIPT = os.path.join(os.path.dirname(__file__), "../../devlithium-finance/scripts/log_expense.py")

PRIORITY_EMOJI = {
    "critical": "🚨",
    "high": "🔴",
    "medium": "🟡",
    "low": "🟢",
}

STATUS_ORDER = ["open", "approved", "scheduled", "in_progress", "resolved"]


def load_kb():
    with open(KB_PATH) as f:
        return json.load(f)


def save_kb(kb):
    kb["_meta"]["last_updated"] = str(date.today())
    with open(KB_PATH, "w") as f:
        json.dump(kb, f, indent=2)


def get_issues(kb):
    return kb["services"]["repair"].setdefault("open_issues", [])


def next_issue_id(issues):
    if not issues:
        return "REP-001"
    nums = []
    for issue in issues:
        try:
            nums.append(int(issue["id"].split("-")[1]))
        except (IndexError, ValueError):
            pass
    return f"REP-{(max(nums) + 1):03d}" if nums else "REP-001"


def age_days(reported_date_str):
    try:
        reported = datetime.strptime(reported_date_str, "%Y-%m-%d").date()
        return (date.today() - reported).days
    except (ValueError, TypeError):
        return 0


def get_room_name(kb, room_id):
    for room in kb.get("rooms", []):
        if room["id"] == room_id:
            return room["name"]
    return room_id


def action_log(kb, args):
    """Log a new repair issue."""
    if not args.description:
        print("ERROR: --description is required for --action log")
        sys.exit(1)

    issues = get_issues(kb)
    issue_id = next_issue_id(issues)
    priority = (args.priority or "medium").lower()
    if priority not in PRIORITY_EMOJI:
        print(f"WARNING: Unknown priority '{priority}', using 'medium'.")
        priority = "medium"

    issue = {
        "id": issue_id,
        "description": args.description,
        "room_id": args.room or "unknown",
        "reported_by": args.reported_by or "u1",
        "reported_date": str(date.today()),
        "priority": priority,
        "status": "open",
        "provider_quotes": [],
        "approved_by": None,
        "scheduled_date": None,
        "resolved_date": None,
        "cost_inr": None,
    }
    issues.append(issue)
    save_kb(kb)

    room_name = get_room_name(kb, issue["room_id"])
    print(f"\n{PRIORITY_EMOJI[priority]} REPAIR ISSUE LOGGED — {issue_id}")
    print(f"{'='*45}")
    print(f"Issue:    {args.description}")
    print(f"Room:     {room_name}")
    print(f"Priority: {priority.upper()}")
    print(f"Status:   open")
    print(f"Date:     {date.today()}")
    if priority in ("critical", "high"):
        print(f"\n⚡ ACTION REQUIRED: Get provider quotes and seek Dev's approval.")
    print()


def action_quote(kb, args):
    """Add a provider quote to an existing issue."""
    if not args.id or not args.provider or args.cost is None:
        print("ERROR: --id, --provider, and --cost are required for --action quote")
        sys.exit(1)

    issues = get_issues(kb)
    issue = next((i for i in issues if i["id"] == args.id), None)
    if not issue:
        print(f"ERROR: Issue {args.id} not found.")
        sys.exit(1)

    quote = {
        "provider": args.provider,
        "cost_inr": float(args.cost),
        "added_date": str(date.today()),
        "verified": args.provider in ("Urban Company", "Sulekha"),
    }
    issue["provider_quotes"].append(quote)
    save_kb(kb)

    quotes = sorted(issue["provider_quotes"], key=lambda q: q["cost_inr"])
    print(f"\n🔧 PROVIDER QUOTES — {args.id}: {issue['description']}")
    print(f"{'='*50}")
    for idx, q in enumerate(quotes, 1):
        verified_tag = "★ Recommended (verified)" if q["verified"] else "⚠️ Unverified"
        print(f"  {idx}. {q['provider']:<22} ₹{q['cost_inr']:,.0f}  {verified_tag}")

    verified_quotes = [q for q in quotes if q["verified"]]
    if verified_quotes:
        best = verified_quotes[0]
        print(f"\nCheapest verified:  {best['provider']} @ ₹{best['cost_inr']:,.0f}")
    cheapest = quotes[0]
    print(f"Cheapest overall:   {cheapest['provider']} @ ₹{cheapest['cost_inr']:,.0f}")

    total_cost = max((q["cost_inr"] for q in quotes), default=0)
    if total_cost > 500 or len(issue["provider_quotes"]) >= 1:
        print(f"\n⚡ Approval needed from Dev (u1) before booking — cost > ₹500 or physical change.")
    print()


def action_approve(kb, args):
    """Mark an issue as approved after resident sign-off."""
    if not args.id:
        print("ERROR: --id is required for --action approve")
        sys.exit(1)

    issues = get_issues(kb)
    issue = next((i for i in issues if i["id"] == args.id), None)
    if not issue:
        print(f"ERROR: Issue {args.id} not found.")
        sys.exit(1)

    issue["status"] = "approved"
    issue["approved_by"] = args.approved_by or "u1"
    if args.provider:
        issue["approved_provider"] = args.provider
    if args.cost is not None:
        issue["cost_inr"] = float(args.cost)
    save_kb(kb)

    print(f"\n✅ REPAIR APPROVED — {args.id}")
    print(f"{'='*45}")
    print(f"Issue:    {issue['description']}")
    print(f"Approved by: {issue['approved_by']}")
    if args.provider:
        print(f"Provider: {args.provider} @ ₹{args.cost:,.0f}")
    print(f"\nNext step: Schedule the appointment using --action schedule")
    print()


def action_schedule(kb, args):
    """Log the scheduled date for a repair."""
    if not args.id or not args.scheduled_date:
        print("ERROR: --id and --scheduled_date are required for --action schedule")
        sys.exit(1)

    issues = get_issues(kb)
    issue = next((i for i in issues if i["id"] == args.id), None)
    if not issue:
        print(f"ERROR: Issue {args.id} not found.")
        sys.exit(1)

    issue["status"] = "scheduled"
    issue["scheduled_date"] = args.scheduled_date
    save_kb(kb)

    room_name = get_room_name(kb, issue["room_id"])
    provider = issue.get("approved_provider", "Provider TBD")
    print(f"\n📅 REPAIR SCHEDULED — {args.id}")
    print(f"{'='*45}")
    print(f"Issue:    {issue['description']}")
    print(f"Room:     {room_name}")
    print(f"Provider: {provider}")
    print(f"Date:     {args.scheduled_date}")
    print(f"\n💬 Notify room occupant to ensure access on {args.scheduled_date}.")
    print()


def action_resolve(kb, args):
    """Mark an issue as resolved and log cost to finance."""
    if not args.id:
        print("ERROR: --id is required for --action resolve")
        sys.exit(1)

    issues = get_issues(kb)
    issue = next((i for i in issues if i["id"] == args.id), None)
    if not issue:
        print(f"ERROR: Issue {args.id} not found.")
        sys.exit(1)

    final_cost = float(args.cost) if args.cost is not None else (issue.get("cost_inr") or 0)
    issue["status"] = "resolved"
    issue["resolved_date"] = str(date.today())
    issue["cost_inr"] = final_cost
    save_kb(kb)

    print(f"\n✅ REPAIR RESOLVED — {args.id}")
    print(f"{'='*45}")
    print(f"Issue:    {issue['description']}")
    print(f"Cost:     ₹{final_cost:,.0f}")
    print(f"Resolved: {date.today()}")

    # Sync cost to devlithium-finance
    if final_cost > 0:
        try:
            result = subprocess.run(
                [
                    sys.executable, FINANCE_SCRIPT,
                    "--category", "repair",
                    "--item", issue["description"][:60],
                    "--amount", str(final_cost),
                    "--paid_by", issue.get("approved_by") or "u1",
                    "--split", "equal",
                ],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                print(f"\n💰 Cost logged to pool fund:")
                print(result.stdout.strip())
            else:
                print(f"\n⚠️ Could not auto-log to finance — log manually:")
                print(f"   python skills/devlithium-finance/scripts/log_expense.py \\")
                print(f"     --category repair --item \"{issue['description']}\" \\")
                print(f"     --amount {final_cost} --paid_by u1 --split equal")
        except FileNotFoundError:
            print(f"\n⚠️ Finance script not found — log manually:")
            print(f"   python skills/devlithium-finance/scripts/log_expense.py \\")
            print(f"     --category repair --item \"{issue['description']}\" \\")
            print(f"     --amount {final_cost} --paid_by u1 --split equal")
    print()


def action_status(kb, args):
    """Show detailed status of a single issue."""
    if not args.id:
        print("ERROR: --id is required for --action status")
        sys.exit(1)

    issues = get_issues(kb)
    issue = next((i for i in issues if i["id"] == args.id), None)
    if not issue:
        print(f"ERROR: Issue {args.id} not found.")
        sys.exit(1)

    room_name = get_room_name(kb, issue["room_id"])
    emoji = PRIORITY_EMOJI.get(issue["priority"], "🔵")
    days_old = age_days(issue["reported_date"])

    print(f"\n🔧 REPAIR STATUS — {issue['id']}")
    print(f"{'='*45}")
    print(f"Description: {issue['description']}")
    print(f"Room:        {room_name}")
    print(f"Priority:    {emoji} {issue['priority'].upper()}")
    print(f"Status:      {issue['status'].upper()}")
    print(f"Reported:    {issue['reported_date']} ({days_old} days ago)")
    print(f"Reported by: {issue['reported_by']}")

    if issue["provider_quotes"]:
        print(f"\nQuotes ({len(issue['provider_quotes'])}):")
        for q in sorted(issue["provider_quotes"], key=lambda x: x["cost_inr"]):
            v = "✓" if q["verified"] else "?"
            print(f"  [{v}] {q['provider']:<20} ₹{q['cost_inr']:,.0f}")

    if issue.get("approved_by"):
        print(f"\nApproved by: {issue['approved_by']}")
        if issue.get("approved_provider"):
            print(f"Provider:    {issue['approved_provider']}")
    if issue.get("scheduled_date"):
        print(f"Scheduled:   {issue['scheduled_date']}")
    if issue.get("resolved_date"):
        print(f"Resolved:    {issue['resolved_date']}")
    if issue.get("cost_inr") is not None:
        print(f"Final cost:  ₹{issue['cost_inr']:,.0f}")

    if issue["status"] == "open" and days_old >= 3:
        print(f"\n⚠️ ESCALATION: Issue open {days_old} days — action overdue!")
    print()


def action_list(kb, args):
    """List all non-resolved repair issues (and summary of resolved)."""
    issues = get_issues(kb)
    today = str(date.today())

    open_issues = [i for i in issues if i["status"] != "resolved"]
    resolved_month = [
        i for i in issues
        if i["status"] == "resolved"
        and (i.get("resolved_date") or "")[:7] == today[:7]
    ]

    print(f"\n🔧 REPAIR ISSUES — {today}")
    print(f"{'='*55}")

    if not open_issues:
        print("  No open issues. House is all clear!")
    else:
        priority_order = ["critical", "high", "medium", "low"]
        open_issues.sort(key=lambda i: (priority_order.index(i.get("priority", "low")), i["reported_date"]))
        for issue in open_issues:
            emoji = PRIORITY_EMOJI.get(issue["priority"], "🔵")
            room_name = get_room_name(kb, issue["room_id"])
            days_old = age_days(issue["reported_date"])
            escalate = " ⚠️ OVERDUE" if (issue["status"] == "open" and days_old >= 3) else ""
            sched = f" → Scheduled {issue['scheduled_date']}" if issue.get("scheduled_date") else ""
            print(f"  {issue['id']}  {emoji} {issue['priority'].upper():<8}  "
                  f"{issue['description'][:30]:<30} ({room_name})  "
                  f"{days_old}d  [{issue['status']}]{sched}{escalate}")

    print(f"{'='*55}")
    print(f"Open: {len(open_issues)} | "
          f"Scheduled: {sum(1 for i in open_issues if i['status'] == 'scheduled')} | "
          f"Resolved this month: {len(resolved_month)}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Devlithium Repair Manager")
    parser.add_argument("--action", required=True,
                        choices=["log", "quote", "approve", "schedule", "resolve", "status", "list"])
    parser.add_argument("--id", help="Issue ID (e.g. REP-001)")
    parser.add_argument("--description", help="Description of the problem")
    parser.add_argument("--room", help="Room ID (e.g. r1, r4)")
    parser.add_argument("--priority", default="medium",
                        choices=["low", "medium", "high", "critical"])
    parser.add_argument("--reported_by", default="u1", help="Resident ID who reported it")
    parser.add_argument("--provider", help="Provider name")
    parser.add_argument("--cost", type=float, help="Cost in INR")
    parser.add_argument("--approved_by", default="u1", help="Resident ID who approved")
    parser.add_argument("--scheduled_date", help="Scheduled date (YYYY-MM-DD)")
    args = parser.parse_args()

    kb = load_kb()

    actions = {
        "log": action_log,
        "quote": action_quote,
        "approve": action_approve,
        "schedule": action_schedule,
        "resolve": action_resolve,
        "status": action_status,
        "list": action_list,
    }
    actions[args.action](kb, args)


if __name__ == "__main__":
    main()
