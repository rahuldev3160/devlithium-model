"""
devlithium-setup: create_kb.py
Creates a blank house_kb.json from the default template.
Run when house_kb.json doesn't exist yet.
"""
import json
import os
from datetime import date

KB_PATH = os.path.join(os.path.dirname(__file__), "../../../data/house_kb.json")
LOG_DIR = os.path.join(os.path.dirname(__file__), "../../../logs")

TEMPLATE = {
    "_meta": {
        "version": "1.0",
        "model": "Devlithium",
        "created": str(date.today()),
        "last_updated": str(date.today()),
        "description": "House Knowledge Base — Devlithium Home Manager"
    },
    "house": {
        "name": "Devlithium House",
        "location": {
            "country": "India", "state": "Rajasthan", "city": "Jaipur",
            "pincode": None, "address_line1": None, "floor": None,
            "gps_lat": None, "gps_lng": None
        },
        "features": {"has_terrace": True, "terrace_area_sqft": None, "solar_panels": False}
    },
    "rooms": [],
    "residents": [],
    "inventory": {"grocery": [], "cleaning_supplies": []},
    "finance": {
        "pool_fund": {
            "currency": "INR", "minimum_balance": 10000, "current_balance": 0,
            "alert_threshold": 12000, "split_method": "equal"
        },
        "expense_log": []
    },
    "services": {
        "repair": {"preferred_provider": "Urban Company", "open_issues": []},
        "cleaning": {"schedule": "weekly", "last_cleaned": None}
    },
    "sustainability": {
        "terrace_farm": {"active": False, "crops": [], "estimated_monthly_savings_inr": 0},
        "rental_potential": {"assessed": False, "estimated_monthly_income_inr": 0}
    },
    "self_learning": {
        "training_start_date": str(date.today()),
        "feedback_sessions": 0,
        "log_file": "logs/daily_log.jsonl"
    }
}

def create_kb():
    os.makedirs(os.path.dirname(KB_PATH), exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    if os.path.exists(KB_PATH):
        print(f"house_kb.json already exists at {KB_PATH}. Skipping creation.")
        return
    with open(KB_PATH, "w") as f:
        json.dump(TEMPLATE, f, indent=2)
    print(f"✅ house_kb.json created at {KB_PATH}")
    # Create empty log file
    log_path = os.path.join(LOG_DIR, "daily_log.jsonl")
    if not os.path.exists(log_path):
        open(log_path, "w").close()
        print(f"✅ daily_log.jsonl initialized at {log_path}")

if __name__ == "__main__":
    create_kb()
