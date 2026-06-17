---
name: devlithium-sustain
description: Use this skill for sustainability analysis, income generation from the house, terrace farming, rental opportunities, solar assessment, or any initiative to reduce costs or generate revenue. Triggers on "terrace farming", "rental income", "solar panels", "reduce electricity bill", "monetize the house", "sustainability report", or "income from home". This skill acts as a strategic planner — it assesses options, models ROI, and recommends the highest-value action.
---

# devlithium-sustain

Strategic sustainability planner for the Devlithium house. Tracks terrace farming, models rental income, assesses solar ROI, and generates weekly pulse reports. Focuses on reducing costs and creating passive income streams.

**Model rule**: Sonnet task (strategic reasoning required). Load only `house_kb.sustainability` and `house_kb.house.features`.

## Data
- Read/Write: `house_kb.json` → `sustainability` section
- Reference: `house_kb.house.features` (solar_panels, has_terrace, terrace_area_sqft)

---

## A. Terrace Farm Management

The house has a top-floor terrace (`house_kb.house.features.has_terrace: true`). Use it to grow vegetables and reduce grocery bills.

### Track a crop
```bash
python skills/devlithium-sustain/scripts/sustain_check.py \
  --action terrace \
  --crop "Tomato" \
  --planted_date 2026-05-01 \
  --harvest_date 2026-07-01 \
  --yield_kg 5 \
  --market_price 40
```

Each crop stored in `house_kb.sustainability.terrace_farm.crops`:
```json
{
  "name": "Tomato",
  "planted_date": "2026-05-01",
  "expected_harvest_date": "2026-07-01",
  "yield_kg": 5,
  "market_price_per_kg_inr": 40,
  "estimated_savings_inr": 200,
  "status": "growing"
}
```

### Terrace farm output
```
🌱 TERRACE FARM STATUS — 2026-05-15
=====================================
Active crops: 3
  Tomato     → Harvest: 2026-07-01 (47 days)   Est. savings: ₹200
  Coriander  → Harvest: 2026-05-25 (10 days)   Est. savings: ₹60  ⏰ Harvest soon!
  Chilli     → Harvest: 2026-08-01 (77 days)   Est. savings: ₹150

Monthly savings estimate: ₹200
Cumulative savings this year: ₹0
```

### Harvest reminder rule
Called by `devlithium-daily` Step 6 (Sustainability Pulse) on Mondays:
- Any crop with `expected_harvest_date` within 14 days → include in daily notification
- Mark crop `status: harvested` when done, log savings to `terrace_farm.estimated_monthly_savings_inr`

### Recommended crops for Jaipur (heat-tolerant, high yield)
| Crop | Season | Avg yield/sqft | Market price |
|------|---------|---------------|--------------|
| Tomato | Oct–Feb | 3 kg | ₹30–60/kg |
| Coriander | Oct–Mar | 0.5 kg | ₹80–120/kg |
| Methi (Fenugreek) | Nov–Feb | 0.3 kg | ₹40–60/kg |
| Chilli | Mar–Jun | 1 kg | ₹60–100/kg |
| Spinach (Palak) | Nov–Feb | 0.5 kg | ₹30–50/kg |

---

## B. Rental Income Assessment

Assess monetization options for the house's spaces. Run a full assessment:

```bash
python skills/devlithium-sustain/scripts/sustain_check.py --action rental
```

### Rentable areas to evaluate:

**1. Terrace rental** (top floor, Jaipur residential area)
- Events (birthday parties, pre-weddings): ₹2,000–5,000 per event, 2–3 events/month
- Parking (if adjacent): ₹500–1,000/month
- Telecom tower lease: ₹5,000–15,000/month (requires structural assessment; long-term)

**2. Spare room rental** (if any resident vacates)
- PG room in Jaipur 302021: ₹4,000–8,000/month
- Only assess when `status: active` resident count < 3

**ROI model for each opportunity:**
```
Opportunity:        Terrace events
Upfront setup cost: ₹5,000 (cleaning, lighting, basic furniture)
Monthly income:     ₹8,000 (2 events × ₹4,000 avg)
Payback period:     1 month
Net annual income:  ₹91,000
Recommendation:     HIGH VALUE — pursue immediately
```

Results written to `house_kb.sustainability.rental_potential.rentable_areas`.

---

## C. Solar Panel Assessment

Check solar feasibility for the Jaipur top-floor terrace:

```bash
python skills/devlithium-sustain/scripts/sustain_check.py --action solar
```

Reference data (`house_kb.house.features.solar_panels`):
- If `false`: model full ROI and recommend
- If `true`: track actual savings vs. bill

**Jaipur solar assumptions** (high-solar zone, Rajasthan):
- Average peak sun hours: 6.5 hours/day (one of India's highest)
- Typical 2kW rooftop system: ₹1,50,000–2,00,000 installed
- Monthly generation: ~240–300 units (kWh)
- Average electricity rate in Jaipur: ₹6–8 per unit
- Monthly savings: ₹1,500–2,500
- Payback period: 5–7 years
- Post-payback net benefit: ₹18,000–30,000/year (system life 25 years)
- MNRE subsidy (2026): up to 40% on first 2kW → reduces install cost by ₹60,000–80,000

**Solar output format:**
```
☀️ SOLAR ASSESSMENT — Devlithium House (Jaipur)
=================================================
Current solar panels:  NO
Current monthly bill:  ₹[amount]

Recommended system:    2kW Rooftop
Install cost:          ₹1,80,000
MNRE subsidy (40%):   -₹72,000
Net cost:              ₹1,08,000
Monthly savings:       ₹2,000
Payback period:        54 months (4.5 years)
Net gain over 25yr:    ₹4,92,000

Recommendation: ✅ HIGH ROI — Submit MNRE subsidy application first.
Next step: Get 2 vendor quotes (Tata Solar, Loom Solar recommended for Jaipur).
```

After assessment, update:
- `house_kb.sustainability.energy.solar_assessed: true`
- `house_kb.sustainability.energy.monthly_bill_avg_inr` (if user provides it)

---

## D. Weekly Sustainability Pulse

Called every Monday by `devlithium-daily` (Step 6):

```bash
python skills/devlithium-sustain/scripts/sustain_check.py --action weekly_pulse
```

Output format:
```
🌿 SUSTAINABILITY PULSE — Week of 2026-05-12
==============================================
Terrace Farm:
  Active crops:    3
  Harvest due:     Coriander (10 days)
  Savings this week: ₹0 (no harvest)

Rental Income:
  This week:       ₹0 (no events booked)
  Pipeline:        1 inquiry pending

Solar:
  Assessed:        No  ← ACTION: Run solar assessment

Top Recommendation:
  → Book terrace event rental for this weekend (potential ₹4,000 income)
  → Plant Coriander batch 2 after current harvest (quick ROI, 30 days)
==============================================
```

### Recommendation engine logic:
1. If terrace farm has no active crops → suggest planting (based on season)
2. If no rental income this month → suggest booking an event
3. If solar not assessed → flag once (not every week)
4. If monthly grocery spend > ₹3,000 → suggest expanding farm area
5. Always output exactly one "Top Recommendation" — the highest expected INR return

---

## Rules
- Never recommend an action costing > ₹500 without flagging it for Dev's approval
- All income projections must show both optimistic and conservative estimates
- Solar assessment is a one-time recommendation — don't re-flag after first mention
- Terrace farm data must be kept current — always ask Dev to update harvest dates
- Sustainability pulse runs Mondays only (checked via `date.today().weekday() == 0`)
