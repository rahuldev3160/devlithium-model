---
name: devlithium-events
description: Use this skill to plan, coordinate, and track events, outings, gatherings, and trips for Devlithium residents. Triggers on "plan a trip", "house party", "birthday reminder", "group outing", "plan Diwali", "book tickets", "who's available on", "plan a trip to [place]", or any social/travel planning request. Checks resident travel preferences, shared contacts, and budget from pool or individual funds. Optimizes for cost and preferred locations.
---

# devlithium-events

Plans, coordinates, and tracks events, trips, gatherings, and occasion reminders for all 3 Devlithium residents.

**Model rule**: Haiku for scheduling and logistics. Sonnet for itinerary planning and destination recommendations.

## Data Sources
- Read: `data/profiles/u1.json`, `u2.json`, `u3.json` → sections: `locations`, `relationships`, `preferences`
- Read: `data/house_kb.json` → `finance.pool_fund` (for budget checks)
- Write: `logs/events_log.jsonl` (one JSON per line per event)

---

## A. Event Types

| Type | Trigger | Notes |
|------|---------|-------|
| Group outing | "let's plan", "all 3 of us" | All residents participate |
| House gathering | "house party", "Diwali", "Holi" | Held at Devlithium House |
| Individual trip | One resident mentions travel | Adjust house routines |
| Occasion reminder | Birthdays, anniversaries | Auto from relationship profiles |

---

## B. Trip Planning Flow

When a trip is requested:

```bash
python skills/devlithium-events/scripts/event_planner.py --action trip_suggestions --participants u1,u2,u3 --budget 5000
```

Steps:
1. Load `locations.travel_preferences.preferred_destinations` from each participating resident
2. Check `locations.upcoming_trips` for scheduling conflicts
3. Find intersection of preferred destinations OR default to top-rated Rajasthan options
4. Suggest top 3 destinations matching shared preferences + budget
5. For each suggestion: estimate travel + accommodation + food per person

**Budget approval gate**: If estimated spend per person > INR 500 from pool → flag for u1 approval before proceeding.

### Embedded Jaipur-Based Trip Knowledge

Use this as baseline for destination suggestions:

**Weekend trips from Jaipur (≤ 2 days):**
| Destination | Distance | Drive Time | Per Person Estimate |
|-------------|----------|-----------|---------------------|
| Pushkar | 145 km | 2.5 hr | INR 1,500–2,500 |
| Ajmer (Dargah) | 135 km | 2 hr | INR 800–1,500 |
| Abhaneri (stepwell) | 95 km | 1.5 hr | INR 500–800 |
| Sambhar Salt Lake | 80 km | 1.5 hr | INR 400–700 |

**Short break (2–3 days):**
| Destination | Distance | Mode | Per Person Estimate |
|-------------|----------|------|---------------------|
| Udaipur | 395 km | Car (5hr) / Bus | INR 3,000–6,000 |
| Jodhpur | 340 km | Car (4.5hr) / Train | INR 2,500–5,000 |
| Mount Abu | 490 km | Car (5.5hr) | INR 3,500–6,500 |
| Ranthambore | 180 km | Car (3hr) | INR 4,000–8,000 (safari incl.) |

**Longer trips (3–5 days):**
| Destination | Mode | Per Person Estimate |
|-------------|------|---------------------|
| Kumbhalgarh | Car (3.5hr) | INR 5,000–9,000 |
| Goa | Train (14–16hr) | INR 8,000–15,000 |
| Manali / Himachal | Bus/Train (16–18hr) | INR 7,000–12,000 |
| Rishikesh/Haridwar | Train (10hr) | INR 4,000–7,000 |

**Budget tips:**
- Always check IRCTC Tatkal vs. advance booking (book 60 days out for best fares)
- OYO/Zostel hostels reduce accommodation 40–60% vs. hotels
- Group travel on own/rented car cheapest for ≤ 400 km trips
- Redbus AC sleeper Jaipur–Jodhpur/Udaipur typically INR 350–600

---

## C. Occasion Calendar

```bash
python skills/devlithium-events/scripts/event_planner.py --action upcoming_occasions
```

Steps:
1. Load `relationships.family[].birthday` (and `.anniversary` if present) from all 3 profiles
2. Also load `relationships.shared_contacts[].birthday` if present
3. List all occasions in the next 30 days sorted by date
4. For each: print name, relation, date, days until
5. Remind 7 days before → via devlithium-notify
6. Remind 1 day before → via devlithium-notify (urgent flag)

Output:
```
UPCOMING OCCASIONS (next 30 days) — [Date]
========================================
[DD Mon]  [Name] ([relation] of [resident]) — Birthday — in X days
[DD Mon]  [Name] — Anniversary — in X days
```

### Major Indian Festival Calendar (Jaipur context)
Pre-load for planning gatherings:
- Holi: March (advance 1 week: colors, sweets, drinks budget ~INR 500/person)
- Teej: July–August (u3 specific if applicable)
- Diwali: October–November (firecrackers optional, diyas/lights, sweets ~INR 1,000/person)
- Dussehra: October (Jaipur has Mela — good group outing)
- New Year (Jan 1): Party or trip — plan 30 days out

---

## D. Plan Event Flow

For a house gathering or outing:

```bash
python skills/devlithium-events/scripts/event_planner.py \
  --action plan_trip \
  --participants u1,u2,u3 \
  --budget 3000 \
  --dates "2026-06-01,2026-06-02"
```

Output includes:
- Recommended destination
- Travel mode + estimated cost
- Accommodation option
- Food estimate
- Total per person
- Budget flag (if > INR 500/person from pool, request u1 approval)

---

## E. Individual Trip — House Adjustment

When one resident is travelling alone:
1. Note trip dates in `locations.upcoming_trips`
2. Pause auto-orders assigned to that resident
3. If milk delivery is resident-specific → pause for trip duration
4. Notify other residents: "Dev is away [dates]. Adjust cooking and routines."

---

## F. Event Log

Every planned or completed event is saved to `logs/events_log.jsonl` (one JSON per line):

```json
{
  "date": "YYYY-MM-DD",
  "event_type": "trip|gathering|outing|occasion",
  "participants": ["u1", "u2"],
  "destination": "Pushkar",
  "budget_inr": 4500,
  "actual_cost_inr": 0,
  "status": "planned|completed|cancelled",
  "notes": ""
}
```

```bash
python skills/devlithium-events/scripts/event_planner.py \
  --action log_event \
  --participants u1,u2,u3 \
  --budget 4500
```

---

## Rules
- Never confirm a group trip without checking all participants' `upcoming_trips` for conflicts
- If budget > INR 500/person from pool → always flag for u1 approval before planning further
- All event logs must include `status` — update to `completed` after the event
- For individual trips: always send house adjustment notice to remaining residents
- Occasion reminders: 7-day alert + 1-day alert — never miss these
