---
name: devlithium-ventures
description: Use this skill to plan, evaluate, and coordinate business ventures, joint investments, side income ideas, and entrepreneurial projects among Devlithium residents. Triggers on "business idea", "start a venture", "side income", "let's invest in", "new project", "should we start X", "evaluate this idea", "who's best for this role", or any entrepreneurial/venture planning request. Acts as a super coordinator — matches skills, pools capital, models ROI, and runs the venture like a professional project manager.
---

# devlithium-ventures

Evaluates business ideas, matches resident skills to roles, pools capital, models ROI, and tracks ventures from idea to profitability.

**Model rule**: Opus for strategic planning. Sonnet for analysis and evaluation. Haiku for tracking and pulse checks.

## Data Sources
- Read: `data/profiles/u1.json`, `u2.json`, `u3.json` → sections: `financial`, `skills_and_expertise`, `venture_interests`
- Read/Write: `data/ventures.json` (create if not exists)

---

## A. Idea Intake & Evaluation

When any resident proposes a venture idea:

```bash
python skills/devlithium-ventures/scripts/venture_coordinator.py \
  --action log_idea \
  --data '{"title":"Tiffin Service","proposed_by":"u2","description":"Homemade tiffin for nearby PGs","capital_required_inr":15000,"expected_monthly_revenue_inr":12000,"risk_level":"low","skill_requirements":["cooking","delivery_coordination"]}'
```

Each idea is logged to `data/ventures.json` with this schema:
```json
{
  "id": "v001",
  "title": "string",
  "proposed_by": "u1|u2|u3",
  "date": "YYYY-MM-DD",
  "stage": "idea|evaluated|active|paused|closed",
  "description": "string",
  "capital_required_inr": 0,
  "expected_monthly_revenue_inr": 0,
  "actual_revenue_inr": 0,
  "actual_expenses_inr": 0,
  "profit_inr": 0,
  "risk_level": "low|medium|high",
  "participants": [],
  "skill_requirements": [],
  "monthly_loss_streak": 0,
  "notes": []
}
```

**Auto-evaluation on intake:**
1. Capital check: is `sum(capital_available_for_ventures_inr)` ≥ `capital_required_inr`?
2. Skill match: does team cover all `skill_requirements`? (see Section B)
3. ROI model: `simple_payback_months = capital_required_inr / expected_monthly_revenue_inr`
4. Risk assessment: flag high-risk ventures if any resident has conservative risk appetite

---

## B. Skill Matching

```bash
python skills/devlithium-ventures/scripts/venture_coordinator.py \
  --action skill_match \
  --venture_id v001
```

Steps:
1. Load `skills_and_expertise` from all 3 profiles
2. For each required skill in the venture:
   - Find which resident covers it
   - If multiple: recommend the most experienced
3. Flag gaps: skill not covered by any resident → "External hire needed"
4. Recommend optimal role assignment

Output:
```
SKILL MATCH — [Venture Title]
Required: cooking        → Covered by: Hanu (u3)
Required: delivery_coord → Covered by: Sunil (u2)
Required: accounting     → GAP — External hire or u1 to learn
Role assignment: u3=Operations, u2=Logistics, u1=Finance
```

---

## C. Venture Sectors — Jaipur Context (Embedded Knowledge)

When suggesting venture ideas, use this as baseline:

### Tier 1: Low Capital, Quick Start
| Venture | Capital Needed | Expected Monthly Revenue | Risk |
|---------|---------------|--------------------------|------|
| Homemade tiffin service | INR 10K–20K | INR 8K–20K | Low |
| Tuition/coaching (Math, Science, English) | INR 2K–5K | INR 8K–25K | Low |
| Tech freelancing (web dev, data) | INR 0–5K | INR 15K–50K | Low |
| Content creation (YouTube, blog) | INR 5K–15K | INR 3K–20K (6mo delay) | Medium |

### Tier 2: Medium Capital, Stable Returns
| Venture | Capital Needed | Expected Monthly Revenue | Risk |
|---------|---------------|--------------------------|------|
| PG room rental (terrace room) | INR 30K–60K (furnish) | INR 5K–9K/month | Low |
| Airbnb (terrace room short-term) | INR 40K–80K (furnish) | INR 8K–15K/month | Medium |
| Terrace farm → sell surplus | INR 5K–15K (setup) | INR 1K–3K/month | Low |
| E-commerce reselling (Amazon/Meesho) | INR 20K–50K | INR 10K–30K | Medium |

### Tier 3: High Capital, High Return
| Venture | Capital Needed | Expected Monthly Revenue | Risk |
|---------|---------------|--------------------------|------|
| Real estate plot (buy + hold + resell) | INR 15L–40L | INR 0 until sale (10–20% CAGR) | Low-Med |
| Real estate plot + development | INR 25L–60L | INR 15K–30K (rental) | Medium |
| Swing trading (equities) | INR 1L–5L | INR 5K–20K | High |

### Jaipur-Specific Opportunities
- **PG/hostel demand**: Very high near MNIT, Rajasthan University, JLN Marg — top-floor flats and terrace rooms in high demand
- **Tiffin services**: Strong demand from tech parks (Sitapura), PG clusters (Malviya Nagar, Mansarovar)
- **Terrace farming**: Municipal support available; surplus sold to neighbors or at Navratna Mandi
- **Artisan reselling**: Jaipur handicrafts (blue pottery, block print) sell well on Etsy/Amazon

---

## D. Venture Tracking

### Weekly Pulse
Run every Monday:
```bash
python skills/devlithium-ventures/scripts/venture_coordinator.py \
  --action weekly_pulse \
  --venture_id v001 \
  --data '{"actual_revenue_inr":9500,"actual_expenses_inr":3200}'
```

Updates `actual_revenue_inr`, `actual_expenses_inr`, `profit_inr` in ventures.json.
If `profit_inr < 0` for 3 consecutive months → set `monthly_loss_streak` counter and auto-flag for review.

### Monthly P&L Report
```bash
python skills/devlithium-ventures/scripts/venture_coordinator.py \
  --action monthly_pl \
  --venture_id v001
```

Output:
```
MONTHLY P&L — [Venture Title] | [Month Year]
Revenue:    INR [amount]
Expenses:   INR [amount]
Profit:     INR [amount]
ROI so far: [%]
Status:     [Profitable | Break-even | Loss (streak: X months)]
Action:     [Continue | Review | PAUSE RECOMMENDED]
```

**Auto-flag rule**: If `monthly_loss_streak >= 3` → recommend pause or close. Present to u1 for decision.

---

## E. Evaluate an Existing Idea

```bash
python skills/devlithium-ventures/scripts/venture_coordinator.py \
  --action evaluate \
  --venture_id v001
```

Full evaluation report includes:
- Capital feasibility (can we afford it?)
- Skill coverage (who does what?)
- ROI timeline (payback in X months)
- Risk rating for group
- Recommendation: Go / Modify / Pass

---

## Rules
- Never approve a venture that requires capital > combined `capital_available_for_ventures_inr` without u1 sign-off
- Always recommend the lowest-capital option first if multiple viable ideas exist
- Every active venture must have at least one designated lead from the residents
- If `monthly_loss_streak >= 3` → auto-flag for pause regardless of resident sentiment
- All venture decisions require agreement from all participating residents
- Track actual vs. expected revenue from month 1 — do not wait for losses to accumulate
