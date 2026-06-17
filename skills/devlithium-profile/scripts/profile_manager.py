#!/usr/bin/env python3
"""
profile_manager.py — Devlithium Profile Manager
Actions: load | update | aggregate | summary
Python 3.9, stdlib only (json, argparse, os, datetime)
All paths relative to project root (two levels above this script).
"""

import argparse
import json
import os
import sys
from datetime import datetime

# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, "..", "..", ".."))
PROFILES_DIR = os.path.join(PROJECT_ROOT, "data", "profiles")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")
DAILY_LOG = os.path.join(LOGS_DIR, "daily_log.jsonl")

VALID_USERS = ("u1", "u2", "u3")
VALID_SECTIONS = ("financial", "goals", "locations", "relationships",
                  "ventures", "preferences", "skills")
VALID_METRICS = ("liquidity", "investable_capital", "shared_goals", "all")


def profile_path(user_id: str) -> str:
    return os.path.join(PROFILES_DIR, f"{user_id}.json")


# ---------------------------------------------------------------------------
# File I/O helpers
# ---------------------------------------------------------------------------

def load_profile(user_id: str) -> dict:
    """Load and return a profile dict. Exits with instructions if missing."""
    path = profile_path(user_id)
    if not os.path.exists(path):
        print(f"[ERROR] Profile not found: {path}")
        print(f"  To create it, add a file at data/profiles/{user_id}.json")
        print(f"  Use the schema from an existing profile as a template.")
        sys.exit(1)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_profile(user_id: str, data: dict) -> None:
    """Write a profile dict back to disk."""
    path = profile_path(user_id)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def deep_merge(base: dict, updates: dict) -> dict:
    """
    Recursively merge `updates` into `base`.
    Lists in `updates` replace lists in `base` entirely (no de-duplication).
    """
    result = base.copy()
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result


# ---------------------------------------------------------------------------
# Log helper
# ---------------------------------------------------------------------------

def append_log(action: str, user_id: str, section: str = "") -> None:
    """Append a minimal entry to daily_log.jsonl."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    entry = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "session_type": "profile",
        "actions_taken": [f"profile {action} — user={user_id}" + (f" section={section}" if section else "")],
        "what_worked": f"profile_manager ran action={action}",
        "what_failed": None,
        "cost_incurred_inr": 0,
        "income_generated_inr": 0,
        "residents_contacted": [user_id],
        "open_items": []
    }
    with open(DAILY_LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


# ---------------------------------------------------------------------------
# Section key mapping
# ---------------------------------------------------------------------------

SECTION_MAP = {
    "financial": "financial",
    "goals": "goals",
    "locations": "locations",
    "relationships": "relationships",
    "ventures": "venture_interests",
    "preferences": "preferences",
    "skills": "skills_and_expertise",
}


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

def action_load(user_id: str) -> None:
    """Pretty-print the full profile."""
    profile = load_profile(user_id)
    print(json.dumps(profile, indent=2, ensure_ascii=False))
    append_log("load", user_id)


def action_update(user_id: str, section: str, data_str: str) -> None:
    """
    Merge `data_str` (JSON) into the given section of the profile.
    Saves immediately after merge.
    """
    if section not in VALID_SECTIONS:
        print(f"[ERROR] Invalid section '{section}'. Valid: {', '.join(VALID_SECTIONS)}")
        sys.exit(1)

    try:
        updates = json.loads(data_str)
    except json.JSONDecodeError as e:
        print(f"[ERROR] Could not parse --data JSON: {e}")
        sys.exit(1)

    profile = load_profile(user_id)
    section_key = SECTION_MAP[section]

    # skills_and_expertise is a list, not a dict — handle separately
    if section_key == "skills_and_expertise":
        if isinstance(updates, list):
            existing = profile.get("skills_and_expertise", [])
            # Extend without duplicates (by value comparison)
            for item in updates:
                if item not in existing:
                    existing.append(item)
            profile["skills_and_expertise"] = existing
        else:
            print("[ERROR] --data for 'skills' section must be a JSON array.")
            sys.exit(1)
    else:
        existing_section = profile.get(section_key, {})
        profile[section_key] = deep_merge(existing_section, updates)

    # Bump last_updated in _meta
    if "_meta" in profile:
        profile["_meta"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")

    save_profile(user_id, profile)
    name = profile.get("_meta", {}).get("name", user_id)
    print(f"[OK] Profile updated — {name} / section: {section}")
    print(f"     Saved to: data/profiles/{user_id}.json")
    append_log("update", user_id, section)


def action_aggregate(metric: str) -> None:
    """
    Load all 3 profiles and compute aggregate metrics.
    Metric: liquidity | investable_capital | shared_goals | all
    """
    if metric not in VALID_METRICS:
        print(f"[ERROR] Invalid metric '{metric}'. Valid: {', '.join(VALID_METRICS)}")
        sys.exit(1)

    profiles = {}
    missing = []
    for uid in VALID_USERS:
        path = profile_path(uid)
        if os.path.exists(path):
            profiles[uid] = load_profile(uid)
        else:
            missing.append(uid)

    if missing:
        print(f"[WARN] Profiles not found for: {', '.join(missing)} — excluded from aggregate.")

    today = datetime.now().strftime("%Y-%m-%d")
    print(f"AGGREGATE REPORT — Devlithium House ({today})")
    print("=" * 52)

    def get_financial(uid):
        return profiles[uid].get("financial", {}) if uid in profiles else {}

    def get_name(uid):
        return profiles[uid].get("_meta", {}).get("name", uid) if uid in profiles else uid

    # --- liquidity ---
    if metric in ("liquidity", "all"):
        print("\n[LIQUIDITY]")
        total = 0
        for uid in VALID_USERS:
            fin = get_financial(uid)
            liq = fin.get("liquidity", {}).get("total_liquid_inr", 0) or 0
            total += liq
            name = get_name(uid)
            print(f"  {name:10s}: Rs.{liq:,.0f}")
        print(f"  {'TOTAL':10s}: Rs.{total:,.0f}")

    # --- investable capital ---
    if metric in ("investable_capital", "all"):
        print("\n[INVESTABLE CAPITAL]")
        total_venture = 0
        for uid in VALID_USERS:
            fin = get_financial(uid)
            # Sum of liquid MF + savings as rough investable proxy
            liq = fin.get("liquidity", {}) or {}
            venture_cap = 0
            if uid in profiles:
                venture_cap = profiles[uid].get("venture_interests", {}).get("capital_available_for_ventures_inr", 0) or 0
            total_venture += venture_cap
            name = get_name(uid)
            print(f"  {name:10s}: Rs.{venture_cap:,.0f} (venture-earmarked)")
        print(f"  {'TOTAL':10s}: Rs.{total_venture:,.0f}")

    # --- shared goals ---
    if metric in ("shared_goals", "all"):
        print("\n[GOALS OVERVIEW]")
        for uid in VALID_USERS:
            if uid not in profiles:
                continue
            name = get_name(uid)
            goals = profiles[uid].get("goals", {}).get("financial", [])
            if goals:
                for g in goals:
                    goal_name = g.get("goal", "unnamed")
                    target = g.get("target_inr", 0) or 0
                    by = g.get("target_date", "?")
                    print(f"  {name:10s}: {goal_name} — Rs.{target:,.0f} by {by}")
            else:
                print(f"  {name:10s}: no financial goals set")

    print()
    append_log("aggregate", "u1", metric)


def _investment_total(fin: dict) -> float:
    """Sum up all investment values from the financial section."""
    total = 0.0
    inv = fin.get("assets", {}).get("investments", {})
    for mf in inv.get("mutual_funds", []):
        total += mf.get("current_value_inr", 0) or 0
    for st in inv.get("stocks", []):
        total += st.get("current_value_inr", 0) or 0
    for fd in inv.get("fd_rd", []):
        total += fd.get("amount_inr", 0) or 0
    gold = inv.get("gold", {})
    total += gold.get("estimated_value_inr", 0) or 0
    for cr in inv.get("crypto", []):
        total += cr.get("current_value_inr", 0) or 0
    ppf_epf = inv.get("ppf_epf", {})
    total += (ppf_epf.get("ppf_balance_inr", 0) or 0)
    total += (ppf_epf.get("epf_balance_inr", 0) or 0)
    return total


def _monthly_emi_total(fin: dict) -> float:
    """Sum up all monthly EMI liabilities."""
    total = 0.0
    liab = fin.get("liabilities", {})
    total += liab.get("home_loan", {}).get("emi_inr", 0) or 0
    total += liab.get("vehicle_loan", {}).get("emi_inr", 0) or 0
    for pl in liab.get("personal_loans", []):
        total += pl.get("emi_inr", 0) or 0
    for cc in liab.get("credit_cards", []):
        total += cc.get("min_due_inr", 0) or 0
    return total


def _asset_count(fin: dict) -> int:
    """Count real estate + vehicle assets."""
    assets = fin.get("assets", {})
    return len(assets.get("real_estate", [])) + len(assets.get("vehicles", []))


def action_summary(user_id: str) -> None:
    """Print a compact one-screen profile overview."""
    profile = load_profile(user_id)
    meta = profile.get("_meta", {})
    fin = profile.get("financial", {})
    goals_section = profile.get("goals", {})
    locations = profile.get("locations", {})
    ventures = profile.get("venture_interests", {})

    name = meta.get("name", user_id)
    today = datetime.now().strftime("%Y-%m-%d")

    # Financial figures
    income = fin.get("monthly_income", {}).get("total_inr", 0) or 0
    liq_data = fin.get("liquidity", {}) or {}
    liquidity = liq_data.get("total_liquid_inr", 0) or 0
    invest_total = _investment_total(fin)
    asset_count = _asset_count(fin)
    emi_total = _monthly_emi_total(fin)

    # Top goal
    financial_goals = goals_section.get("financial", [])
    top_goal_str = "not set"
    if financial_goals:
        g = financial_goals[0]
        top_goal_str = f"{g.get('goal', '?')} by {g.get('target_date', '?')}"

    # Next trip
    trips = locations.get("travel_preferences", {}).get("upcoming_trips", [])
    trip_str = "none planned"
    if trips:
        t = trips[0]
        trip_str = f"{t.get('destination', '?')} on {t.get('dates', '?')}"

    # Ventures
    open_ventures = ventures.get("open_to_joint_ventures", False)
    venture_capital = ventures.get("capital_available_for_ventures_inr", 0) or 0

    print(f"PROFILE SUMMARY — {name} ({today})")
    print("=" * 52)
    print(f"Liquidity        : Rs.{liquidity:,.0f}  |  Monthly income: Rs.{income:,.0f}")
    print(f"Investments      : Rs.{invest_total:,.0f}")
    print(f"Assets           : {asset_count} item(s)  |  Monthly EMIs: Rs.{emi_total:,.0f}")
    print(f"Top goal         : {top_goal_str}")
    print(f"Next trip        : {trip_str}")
    print(f"Open to ventures : {'Yes' if open_ventures else 'No'}  |  Capital available: Rs.{venture_capital:,.0f}")
    print()
    append_log("summary", user_id)


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------

def parse_args():
    parser = argparse.ArgumentParser(
        description="Devlithium Profile Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python profile_manager.py --action load --user u1
  python profile_manager.py --action summary --user u2
  python profile_manager.py --action update --user u1 --section financial --data '{"monthly_income": {"total_inr": 80000}}'
  python profile_manager.py --action update --user u1 --section skills --data '["Python", "Finance"]'
  python profile_manager.py --action aggregate --metric liquidity
  python profile_manager.py --action aggregate --metric all
        """
    )
    parser.add_argument("--action", required=True,
                        choices=["load", "update", "aggregate", "summary"],
                        help="Action to perform")
    parser.add_argument("--user", default="u1",
                        choices=list(VALID_USERS),
                        help="Resident user ID (default: u1)")
    parser.add_argument("--section",
                        choices=list(VALID_SECTIONS),
                        help="Profile section to update (required for --action update)")
    parser.add_argument("--data",
                        help="JSON string with update values (required for --action update)")
    parser.add_argument("--metric",
                        choices=list(VALID_METRICS),
                        default="all",
                        help="Metric to aggregate (for --action aggregate, default: all)")
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    args = parse_args()

    if args.action == "load":
        action_load(args.user)

    elif args.action == "update":
        if not args.section:
            print("[ERROR] --section is required for --action update")
            sys.exit(1)
        if not args.data:
            print("[ERROR] --data is required for --action update")
            sys.exit(1)
        action_update(args.user, args.section, args.data)

    elif args.action == "aggregate":
        action_aggregate(args.metric)

    elif args.action == "summary":
        action_summary(args.user)


if __name__ == "__main__":
    main()
