"""
devlithium-daily: write_log.py
Appends a new entry to daily_log.jsonl.
Usage: python write_log.py --date 2026-05-15 --session_type daily --actions "checked inventory, sent notification" --what_worked "all checks passed" --what_failed "none" --cost 0 --income 0 --open_items "reorder milk"
"""
import json, argparse, os
from datetime import date

LOG_PATH = os.path.join(os.path.dirname(__file__), "../../../logs/daily_log.jsonl")

def write_log(entry):
    os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)
    with open(LOG_PATH, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"✅ Log entry written for {entry['date']}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", default=str(date.today()))
    parser.add_argument("--session_type", default="daily")
    parser.add_argument("--actions", default="")
    parser.add_argument("--what_worked", default="")
    parser.add_argument("--what_failed", default=None)
    parser.add_argument("--cost", type=float, default=0)
    parser.add_argument("--income", type=float, default=0)
    parser.add_argument("--residents_contacted", default="")
    parser.add_argument("--open_items", default="")
    args = parser.parse_args()

    entry = {
        "date": args.date,
        "session_type": args.session_type,
        "actions_taken": [a.strip() for a in args.actions.split(",") if a.strip()],
        "what_worked": args.what_worked,
        "what_failed": args.what_failed,
        "cost_incurred_inr": args.cost,
        "income_generated_inr": args.income,
        "residents_contacted": [r.strip() for r in args.residents_contacted.split(",") if r.strip()],
        "open_items": [o.strip() for o in args.open_items.split(",") if o.strip()]
    }
    write_log(entry)
