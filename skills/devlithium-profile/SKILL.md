---
name: devlithium-profile
description: Use this skill to collect, update, or view any resident's personal profile — financial assets, investment portfolio, monthly income, liquidity, long-term goals, travel preferences, relationships, or venture interests. Triggers on "update my profile", "add my investments", "set my goals", "I own a car/house/stocks", "my salary is", "I want to buy a house by", "update [resident] profile", "what do we know about Sunil", or any personal data update. Reads/writes to data/profiles/[user_id].json. Privacy enforced: only u1 (admin) can view others' full profiles.
---

# devlithium-profile

Manages personal profiles for all 3 residents. Handles data collection, updates, and cross-profile aggregation for joint planning.

**Model rule**: Haiku for data I/O (load, update, write). Sonnet for cross-profile analysis and aggregation.

---

## Privacy Rules

- Each resident can only see and edit their own profile
- u1 (Dev / admin) can view all profiles in aggregate for joint planning
- Never expose u2/u3 personal financial data to each other without explicit consent from the data owner
- When aggregating for u1, anonymize individual contributions if requested

---

## Data File

`data/profiles/[user_id].json` — one file per resident (u1, u2, u3)

Schema sections: `_meta`, `financial` (income, assets, liabilities, liquidity, risk_appetite), `goals` (financial, lifestyle, career, house_exit_plan), `locations` (work, commute, travel_preferences), `relationships` (family, emergency_contacts, shared_contacts, professional_contacts), `skills_and_expertise`, `venture_interests`, `preferences`

---

## Profile Collection Flow

### Step 1: Identify User

Determine which resident is updating their profile. Default to u1 if not specified. Resolve aliases:
- "Dev" or "u1" → u1
- "Sunil" / "Dhelya" / "u2" → u2
- "Hanu" / "u3" → u3

### Step 2: Load Existing Profile

```bash
python skills/devlithium-profile/scripts/profile_manager.py --action load --user u1
```

### Step 3: Identify Incomplete Sections

Scan loaded profile for fields still `null`, `0`, or `"FILL_IN"`. Group by section. Ask ONE section at a time — never dump the full JSON at the user.

**Collection prompts (natural language only):**

| Section | Prompt |
|---------|--------|
| Financial | "What's your approximate monthly income? Do you have any investments — mutual funds, stocks, FD, or gold?" |
| Assets | "Do you own any property or vehicles outside this house?" |
| Liquidity | "Roughly how much do you keep in savings or current account at any time?" |
| Goals | "What's your biggest financial goal right now, and by when do you want to hit it?" |
| Locations | "Where do you work or commute to? Any trips planned in the next 3 months?" |
| Relationships | "Any family members whose birthdays or important events the model should track?" |
| Ventures | "Are you open to joint investments with housemates? Any business ideas you're working on?" |

### Step 4: Write Updates

Save after each section — do not wait for full profile completion.

```bash
python skills/devlithium-profile/scripts/profile_manager.py \
  --action update \
  --user u1 \
  --section financial \
  --data '{"monthly_income": {"total_inr": 80000}}'
```

Supported `--section` values: `financial`, `goals`, `locations`, `relationships`, `ventures`, `preferences`, `skills`

### Step 5: Cross-Profile Aggregate (Admin Only — u1)

When u1 asks "what's our combined liquidity", "can we afford a joint investment", or similar:

```bash
python skills/devlithium-profile/scripts/profile_manager.py --action aggregate --metric liquidity
```

Supported `--metric` values: `liquidity`, `investable_capital`, `shared_goals`, `all`

Returns: total across all 3 residents, individual contributions (anonymized unless u1 explicitly requests named breakdown).

---

## Summary View

Print a compact one-screen profile overview:

```bash
python skills/devlithium-profile/scripts/profile_manager.py --action summary --user u1
```

**Output format:**
```
PROFILE SUMMARY — [Name] ([date])

Liquidity: Rs.[amount] | Monthly income: Rs.[amount]
Investments: Rs.[total value]
Assets: [N items] | Liabilities: Rs.[total EMIs/month]
Top goal: [goal] by [date]
Next trip: [destination] on [dates]
Open to ventures: [Yes/No] | Capital available: Rs.[amount]
```

---

## Rules

- Always confirm back to the user what was saved, in plain English — never echo raw JSON
- Never write to another resident's profile without their explicit instruction
- If a profile file does not exist yet, print setup instructions — do not crash
- Partial updates are fine; the script merges into the existing JSON, it does not overwrite the whole file
- Run `--action summary` after every update session so the resident can verify their data
- Log the update action to `logs/daily_log.jsonl` with session_type `"profile"`
