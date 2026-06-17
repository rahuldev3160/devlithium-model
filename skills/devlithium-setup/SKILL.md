---
name: devlithium-setup
description: Use this skill to set up or update the Devlithium Home Manager for a house. Triggers when the user wants to onboard a new house, add a resident, update house details, upload house photos for room mapping, fill in the house_kb.json, register the pool fund, or configure the home manager for the first time. Also triggers for "start Devlithium", "configure my house", "add roommate", or "update house details". This is the foundation skill — run it before any other Devlithium skill.
---

# devlithium-setup

This skill bootstraps the Devlithium Home Manager by collecting house data and writing it to `house_kb.json`.

## When This Runs
- First-time setup of a new house
- Adding or removing a resident
- Updating house details (address, rooms, inventory catalog)
- Linking a new service or API

## Data File
Always read and write to: `data/house_kb.json`
If the file doesn't exist, create it from scratch using the template in `scripts/create_kb.py`.

---

## Setup Flow

### Step 1: Load or Create house_kb.json
Read `data/house_kb.json`. If it doesn't exist, run:
```bash
python skills/devlithium-setup/scripts/create_kb.py
```

### Step 2: Identify what's incomplete
Check for all fields with value `"FILL_IN"` or `null`. Group them by section:
- House location (address, pincode, GPS)
- Room details (area, occupant assignments)
- Resident profiles (names, phones, emails, fund shares)
- Finance (pool fund current balance, fixed costs)
- Services (cleaning schedule, delivery app preferences)

### Step 3: Collect missing data from the user
Ask in natural language — do NOT dump a JSON form. Ask one section at a time:

**Example prompts:**
- "What's the full address and pincode of the house?"
- "How many rooms does it have, and who stays in which room?"
- "What are the names and contact details for the other 2 residents?"
- "How much is currently in the shared pool fund?"

Accept photos of the house for room mapping — note layout and dimensions mentioned by user. Estimate room areas if not provided.

### Step 4: Write updates to house_kb.json
After collecting each section, immediately write the data back to `data/house_kb.json`. Don't wait until all data is collected to save.

### Step 5: Confirm & summarize
Show the user a clean summary of what was set up. Flag any sections still incomplete (marked as optional vs. required).

### Step 6: Initialize the daily log
Create `logs/daily_log.jsonl` with a first entry:
```json
{"date": "TODAY", "session_type": "setup", "actions_taken": ["house_kb initialized", "N residents registered"], "what_worked": "setup complete", "what_failed": null, "cost_incurred_inr": 0, "income_generated_inr": 0, "residents_contacted": ["u1"], "open_items": ["fill in missing fields: X, Y, Z"]}
```

---

## Adding a New Resident

1. Assign a new user ID (u4, u5, etc.)
2. Collect: name, phone, email, room assignment, dietary preferences
3. Recalculate `fund_share_pct` for all residents (split equally unless agreed otherwise)
4. Add to `residents` array in house_kb.json
5. Notify existing residents via devlithium-notify

## Removing a Resident

1. Mark resident as `"status": "inactive"` — never delete (preserve expense history)
2. Redistribute their `fund_share_pct` equally among active residents
3. Log the change in daily_log.jsonl

---

## Output on Completion
```
✅ Devlithium Setup Complete
House: [name], [city]
Residents: [n] registered
Inventory items: [n] tracked
Pool fund: ₹[amount]
Missing: [list of still-incomplete fields or "none"]
Next step: Run devlithium-daily to begin automation.
```
