"""
devlithium-events: event_planner.py
Plans, coordinates, and logs events, trips, and occasion reminders for Devlithium residents.
Usage:
  python event_planner.py --action trip_suggestions --participants u1,u2,u3 --budget 5000
  python event_planner.py --action upcoming_occasions
  python event_planner.py --action plan_trip --participants u1,u2 --budget 3000 --dates "2026-06-01,2026-06-02"
  python event_planner.py --action log_event --participants u1,u2,u3 --budget 4500
"""
import json
import argparse
import os
from datetime import date, datetime, timedelta

PROFILES_DIR = os.path.join(os.path.dirname(__file__), "../../../data/profiles")
KB_PATH = os.path.join(os.path.dirname(__file__), "../../../data/house_kb.json")
EVENTS_LOG = os.path.join(os.path.dirname(__file__), "../../../logs/events_log.jsonl")

USERS = ["u1", "u2", "u3"]
USER_NAMES = {"u1": "Dev", "u2": "Sunil", "u3": "Hanu"}

# Embedded trip knowledge — Jaipur-based
TRIP_OPTIONS = [
    {
        "destination": "Pushkar",
        "distance_km": 145,
        "drive_hours": 2.5,
        "duration": "1-2 days",
        "type": "weekend",
        "per_person_min": 1500,
        "per_person_max": 2500,
        "highlights": "Brahma temple, camel fair, ghats, markets",
        "mode": "Car/Bus"
    },
    {
        "destination": "Ajmer",
        "distance_km": 135,
        "drive_hours": 2.0,
        "duration": "1 day",
        "type": "weekend",
        "per_person_min": 800,
        "per_person_max": 1500,
        "highlights": "Dargah Sharif, Ana Sagar lake, Adhai Din ka Jhonpra",
        "mode": "Car/Bus"
    },
    {
        "destination": "Abhaneri",
        "distance_km": 95,
        "drive_hours": 1.5,
        "duration": "Half day",
        "type": "weekend",
        "per_person_min": 500,
        "per_person_max": 800,
        "highlights": "Chand Baori stepwell (iconic), Harshat Mata temple",
        "mode": "Car"
    },
    {
        "destination": "Udaipur",
        "distance_km": 395,
        "drive_hours": 5.0,
        "duration": "2-3 days",
        "type": "short_break",
        "per_person_min": 3000,
        "per_person_max": 6000,
        "highlights": "Lake Pichola, City Palace, local cuisine, boating",
        "mode": "Car/Bus/Train"
    },
    {
        "destination": "Jodhpur",
        "distance_km": 340,
        "drive_hours": 4.5,
        "duration": "2-3 days",
        "type": "short_break",
        "per_person_min": 2500,
        "per_person_max": 5000,
        "highlights": "Mehrangarh Fort, blue city, clock tower market",
        "mode": "Car/Train"
    },
    {
        "destination": "Mount Abu",
        "distance_km": 490,
        "drive_hours": 5.5,
        "duration": "2-3 days",
        "type": "short_break",
        "per_person_min": 3500,
        "per_person_max": 6500,
        "highlights": "Nakki Lake, Dilwara Jain temples, hill station cool weather",
        "mode": "Car/Bus"
    },
    {
        "destination": "Ranthambore",
        "distance_km": 180,
        "drive_hours": 3.0,
        "duration": "2 days",
        "type": "short_break",
        "per_person_min": 4000,
        "per_person_max": 8000,
        "highlights": "Tiger safari, Ranthambore Fort, wildlife",
        "mode": "Car/Train"
    },
    {
        "destination": "Goa",
        "distance_km": 1500,
        "drive_hours": None,
        "duration": "4-5 days",
        "type": "long",
        "per_person_min": 8000,
        "per_person_max": 15000,
        "highlights": "Beaches, seafood, nightlife, water sports",
        "mode": "Train (14-16hr)"
    },
    {
        "destination": "Manali",
        "distance_km": 1100,
        "drive_hours": None,
        "duration": "5-6 days",
        "type": "long",
        "per_person_min": 7000,
        "per_person_max": 12000,
        "highlights": "Rohtang Pass, Solang Valley, adventure sports, snow",
        "mode": "Bus/Train+Bus"
    },
    {
        "destination": "Rishikesh",
        "distance_km": 530,
        "drive_hours": 9.0,
        "duration": "2-3 days",
        "type": "adventure",
        "per_person_min": 8000,
        "per_person_max": 13000,
        "highlights": "River rafting Grade 3-5 (16km stretch), bungee jumping (83m India's highest), Ganga Aarti at Triveni Ghat, Lakshman Jhula, scenic NH58 bike route through Shivalik foothills",
        "mode": "Bike (NH48 via Delhi/Haridwar)",
        "solo_notes": "Ideal solo bike trip. Leave Jaipur 5am, reach by 2pm via Alwar-Delhi-Haridwar. Rafting operators: Shivpuri beach (16km stretch). Best season: Oct-Jun (avoid monsoon Jul-Sep).",
        "activities": ["river_rafting", "bungee_jumping", "bike_ride"],
        "rafting_cost_inr": {"min": 1500, "max": 2000, "notes": "Full day Grade 3-5, 16km stretch, lunch included"},
        "bungee_cost_inr": 3500
    },
]


def load_profile(uid):
    path = os.path.join(PROFILES_DIR, f"{uid}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def load_kb_finance():
    if not os.path.exists(KB_PATH):
        return {}
    with open(KB_PATH) as f:
        kb = json.load(f)
    return kb.get("finance", {})


def ensure_logs_dir():
    logs_dir = os.path.dirname(EVENTS_LOG)
    if not os.path.exists(logs_dir):
        os.makedirs(logs_dir)


def append_event_log(entry):
    ensure_logs_dir()
    with open(EVENTS_LOG, "a") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def parse_participants(participants_str):
    if not participants_str:
        return USERS
    return [p.strip() for p in participants_str.split(",") if p.strip()]


def trip_suggestions(participants_str, budget_per_person):
    participants = parse_participants(participants_str)
    names = [USER_NAMES.get(p, p) for p in participants]

    print(f"\nTRIP SUGGESTIONS — {', '.join(names)} | {date.today()}")
    print("=" * 60)
    print(f"Budget per person: INR {budget_per_person:,.0f}")

    # Check for conflicts
    all_conflicts = []
    for uid in participants:
        profile = load_profile(uid)
        if not profile:
            continue
        trips = profile.get("locations", {}).get("travel_preferences", {}).get("upcoming_trips", [])
        if trips:
            for t in trips:
                all_conflicts.append(f"  {USER_NAMES.get(uid, uid)}: {t}")

    if all_conflicts:
        print("\nScheduling conflicts found:")
        for c in all_conflicts:
            print(c)
        print()

    # Filter by budget
    affordable = [
        opt for opt in TRIP_OPTIONS
        if opt["per_person_min"] <= budget_per_person
    ]

    if not affordable:
        print(f"No destinations found within INR {budget_per_person:,.0f}/person.")
        print("Consider increasing budget or planning a local outing.")
        return

    print(f"\nTop trip options within budget:\n")
    shown = 0
    for opt in affordable:
        if shown >= 3:
            break
        drive_info = f"{opt['drive_hours']}hr drive" if opt['drive_hours'] else opt['mode']
        print(f"Option {shown + 1}: {opt['destination']} ({opt['distance_km']} km — {drive_info})")
        print(f"  Duration:   {opt['duration']}")
        print(f"  Budget:     INR {opt['per_person_min']:,} – {opt['per_person_max']:,} per person")
        print(f"  Mode:       {opt['mode']}")
        print(f"  Highlights: {opt['highlights']}")
        if opt["per_person_min"] * len(participants) > 500:
            print(f"  APPROVAL:   Estimated total > INR 500/person from pool — u1 approval required")
        print()
        shown += 1

    if budget_per_person > 500:
        total_est = affordable[0]["per_person_min"] * len(participants) if affordable else 0
        print(f"Budget alert: Spend per person > INR 500 — flag for u1 approval before booking.")
    print()


def plan_trip(participants_str, budget_per_person, dates_str):
    participants = parse_participants(participants_str)
    names = [USER_NAMES.get(p, p) for p in participants]
    n = len(participants)

    print(f"\nTRIP PLAN — {', '.join(names)}")
    print("=" * 60)
    print(f"Dates:             {dates_str or 'TBD'}")
    print(f"Participants:      {', '.join(names)} ({n} people)")
    print(f"Budget/person:     INR {budget_per_person:,.0f}")
    print(f"Total budget:      INR {budget_per_person * n:,.0f}")

    # Suggest best fit
    affordable = [
        opt for opt in TRIP_OPTIONS
        if opt["per_person_min"] <= budget_per_person
    ]

    if not affordable:
        print("\nNo options within budget. Consider local outing or increase budget.")
        return

    best = affordable[0]
    print(f"\nRecommended:       {best['destination']}")
    print(f"Distance:          {best['distance_km']} km")
    print(f"Travel:            {best['mode']}")
    print(f"Duration:          {best['duration']}")
    print(f"Est. cost/person:  INR {best['per_person_min']:,} – {best['per_person_max']:,}")
    print(f"Est. total:        INR {best['per_person_min'] * n:,} – {best['per_person_max'] * n:,}")
    print(f"\nHighlights: {best['highlights']}")

    if budget_per_person > 500:
        print(f"\nAPPROVAL REQUIRED: Per-person cost > INR 500 from pool — awaiting u1 sign-off.")

    # Auto log
    entry = {
        "date": str(date.today()),
        "event_type": "trip",
        "participants": participants,
        "destination": best["destination"],
        "budget_inr": best["per_person_min"] * n,
        "actual_cost_inr": 0,
        "status": "planned",
        "notes": f"Trip dates: {dates_str or 'TBD'}"
    }
    append_event_log(entry)
    print(f"\nLogged to events_log.jsonl (status: planned)")
    print()


def upcoming_occasions():
    today = date.today()
    horizon = today + timedelta(days=30)

    print(f"\nUPCOMING OCCASIONS (next 30 days) — {today}")
    print("=" * 55)

    occasions = []

    for uid in USERS:
        profile = load_profile(uid)
        if not profile:
            continue
        name = profile["_meta"]["name"]
        relationships = profile.get("relationships", {})

        # Family birthdays
        for member in relationships.get("family", []):
            bday_str = member.get("birthday")
            if not bday_str:
                continue
            try:
                # Parse birthday — normalize to current year
                bday_parsed = datetime.strptime(bday_str, "%Y-%m-%d").date()
                bday_this_year = bday_parsed.replace(year=today.year)
                if bday_this_year < today:
                    bday_this_year = bday_this_year.replace(year=today.year + 1)
                if today <= bday_this_year <= horizon:
                    days_until = (bday_this_year - today).days
                    occasions.append({
                        "date": bday_this_year,
                        "days_until": days_until,
                        "label": f"{member.get('name', 'Unknown')} ({member.get('relation', 'family')} of {name}) — Birthday",
                        "resident": uid,
                        "remind_7d": days_until == 7,
                        "remind_1d": days_until == 1
                    })
            except ValueError:
                continue

        # Shared contacts
        for contact in relationships.get("shared_contacts", []):
            bday_str = contact.get("birthday")
            if not bday_str:
                continue
            try:
                bday_parsed = datetime.strptime(bday_str, "%Y-%m-%d").date()
                bday_this_year = bday_parsed.replace(year=today.year)
                if bday_this_year < today:
                    bday_this_year = bday_this_year.replace(year=today.year + 1)
                if today <= bday_this_year <= horizon:
                    days_until = (bday_this_year - today).days
                    occasions.append({
                        "date": bday_this_year,
                        "days_until": days_until,
                        "label": f"{contact.get('name', 'Unknown')} (shared contact) — Birthday",
                        "resident": uid,
                        "remind_7d": days_until == 7,
                        "remind_1d": days_until == 1
                    })
            except ValueError:
                continue

    if not occasions:
        print("No upcoming occasions in the next 30 days.")
        print("Add birthdays to data/profiles/{uid}.json under relationships.family[].birthday")
        return

    occasions.sort(key=lambda x: x["date"])
    for occ in occasions:
        day_str = occ["date"].strftime("%d %b")
        days = occ["days_until"]
        alert = ""
        if days == 1:
            alert = " *** TOMORROW — URGENT ***"
        elif days == 7:
            alert = " [7-day reminder]"
        print(f"  {day_str}  {occ['label']} — in {days} day(s){alert}")

    print()
    print("Reminders: devlithium-notify sends alerts at 7 days and 1 day before each occasion.")
    print()


def solo_trip(uid, budget, dates_str, activities=None):
    profile = load_profile(uid)
    name = USER_NAMES.get(uid, uid)
    activities = activities or []

    print(f"\nSOLO TRIP PLAN — {name} | {date.today()}")
    print("=" * 60)
    print(f"Dates:         {dates_str or 'TBD'}")
    print(f"Budget:        INR {budget:,.0f}")
    print(f"Activities:    {', '.join(activities) if activities else 'any'}")

    # Match destinations by activity preference
    matched = []
    for opt in TRIP_OPTIONS:
        opt_activities = opt.get("activities", [])
        if any(a in opt_activities for a in activities):
            matched.append(opt)

    if not matched:
        matched = [opt for opt in TRIP_OPTIONS if opt["per_person_min"] <= budget]

    matched = [opt for opt in matched if opt["per_person_min"] <= budget]

    if not matched:
        print(f"\nNo destinations match within INR {budget:,.0f}. Consider increasing budget.")
        return

    best = matched[0]
    fuel_cost = round((best["distance_km"] * 2) / 38 * 104)  # RE Meteor ~38kmpl, petrol ~₹104/L
    accommodation = 3000  # 2 nights budget room
    food = 2000
    misc = 800

    activity_costs = 0
    activity_lines = []
    if "river_rafting" in activities and "rafting_cost_inr" in best:
        rc = best["rafting_cost_inr"]
        activity_costs += rc["min"]
        activity_lines.append(f"  Rafting (Grade 3–5, 16km):  INR {rc['min']:,}–{rc['max']:,}  ({rc['notes']})")
    if "bungee_jumping" in activities and "bungee_cost_inr" in best:
        activity_lines.append(f"  Bungee jumping (83m):        INR {best['bungee_cost_inr']:,}  (optional)")

    total_min = fuel_cost + accommodation + activity_costs + food + misc

    print(f"\nRecommended:   {best['destination']} ({best['distance_km']} km from Jaipur)")
    print(f"Route:         {best['mode']}")
    print(f"Duration:      {best['duration']}")
    print(f"Highlights:    {best['highlights']}")
    if best.get("solo_notes"):
        print(f"\nSolo tip:      {best['solo_notes']}")

    print(f"\n--- Budget Breakdown ---")
    print(f"  Fuel (both ways, ~{best['distance_km']*2}km):   INR {fuel_cost:,}")
    print(f"  Accommodation (2 nights):   INR {accommodation:,}")
    print(f"  Food (3 days):              INR {food:,}")
    print(f"  Tolls + misc:               INR {misc:,}")
    for line in activity_lines:
        print(line)
    print(f"  ---")
    print(f"  Estimated total:            INR {total_min:,}–{total_min + 2000:,}")
    print(f"  Budget remaining (est.):    INR {budget - total_min:,}–{budget - total_min + 2000:,}")

    print(f"\nHouse adjustment: Notifying housemates that {name} is away {dates_str}.")

    # Log the event
    entry = {
        "date": str(date.today()),
        "event_type": "solo_trip",
        "participants": [uid],
        "destination": best["destination"],
        "budget_inr": budget,
        "actual_cost_inr": 0,
        "status": "planned",
        "dates": dates_str,
        "activities": activities,
        "notes": f"Solo bike trip. Exam ends 4pm May 24 — departure May 25 at 5am. {best.get('solo_notes', '')}"
    }
    append_event_log(entry)
    print(f"\nLogged to events_log.jsonl (status: planned)")
    print()


def log_event(participants_str, budget, destination="", event_type="outing", notes=""):
    participants = parse_participants(participants_str)
    entry = {
        "date": str(date.today()),
        "event_type": event_type,
        "participants": participants,
        "destination": destination,
        "budget_inr": budget,
        "actual_cost_inr": 0,
        "status": "planned",
        "notes": notes
    }
    append_event_log(entry)
    names = [USER_NAMES.get(p, p) for p in participants]
    print(f"\nEvent logged to events_log.jsonl")
    print(f"  Type:         {event_type}")
    print(f"  Participants: {', '.join(names)}")
    print(f"  Destination:  {destination or 'TBD'}")
    print(f"  Budget:       INR {budget:,.0f}")
    print(f"  Status:       planned")
    print()


def main():
    parser = argparse.ArgumentParser(description="Devlithium Event Planner")
    parser.add_argument(
        "--action",
        required=True,
        choices=["plan_trip", "upcoming_occasions", "log_event", "trip_suggestions", "solo_trip"],
        help="Action to perform"
    )
    parser.add_argument(
        "--participants",
        default="u1,u2,u3",
        help="Comma-separated user IDs e.g. u1,u2"
    )
    parser.add_argument(
        "--budget",
        type=float,
        default=3000,
        help="Budget per person in INR"
    )
    parser.add_argument(
        "--dates",
        default="",
        help="Trip dates e.g. '2026-06-01,2026-06-02'"
    )
    parser.add_argument(
        "--destination",
        default="",
        help="Destination name (for log_event)"
    )
    parser.add_argument(
        "--event_type",
        default="outing",
        help="Event type: trip|gathering|outing|occasion"
    )
    parser.add_argument(
        "--notes",
        default="",
        help="Optional notes for the event log"
    )
    parser.add_argument(
        "--activities",
        default="",
        help="Comma-separated activity preferences e.g. river_rafting,bungee_jumping,bike_ride"
    )
    args = parser.parse_args()

    if args.action == "trip_suggestions":
        trip_suggestions(args.participants, args.budget)
    elif args.action == "plan_trip":
        plan_trip(args.participants, args.budget, args.dates)
    elif args.action == "upcoming_occasions":
        upcoming_occasions()
    elif args.action == "log_event":
        log_event(args.participants, args.budget, args.destination, args.event_type, args.notes)
    elif args.action == "solo_trip":
        activities = [a.strip() for a in args.activities.split(",") if a.strip()]
        solo_trip(args.participants.split(",")[0], args.budget, args.dates, activities)


if __name__ == "__main__":
    main()
