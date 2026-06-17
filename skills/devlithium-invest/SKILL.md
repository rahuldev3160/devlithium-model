---
name: devlithium-invest
description: Use this skill for all financial analysis, investment recommendations, joint investment decisions, wealth tracking, and financial planning for Devlithium residents. Triggers on "should we invest together", "what should I do with ₹X", "joint investment", "SIP recommendation", "financial health check", "can we afford X", "pool money for investment", "net worth update", or any investment/wealth planning request. Acts as a professional finance expert — analyzes individual profiles, identifies joint opportunities, models ROI, and recommends the optimal move. Requires Sonnet model for reasoning.
---

# devlithium-invest

Provides professional financial analysis, investment recommendations, and wealth planning for all 3 Devlithium residents — individually and jointly.

**Model rule**: Sonnet required (reasoning-heavy). Load only needed profile sections from `data/profiles/`.

## Data Sources
- Read: `data/profiles/u1.json`, `u2.json`, `u3.json` → sections: `financial`, `goals`, `venture_interests`
- Write: append notes/analysis summaries to profile `goals.financial[]` if directed by user

---

## A. Individual Financial Health Check

Run for one or all residents.

```bash
python skills/devlithium-invest/scripts/invest_advisor.py --action health_check --user u1
python skills/devlithium-invest/scripts/invest_advisor.py --action health_check --user all
```

For each resident, calculate and report:

1. **Net Worth** = total assets (real estate + investments + gold + PPF/EPF + vehicles) − total liabilities (loans + credit cards)
2. **Monthly Surplus** = monthly income − all EMIs − estimated monthly expenses
3. **Liquidity Ratio** = total_liquid_inr / (monthly expenses × 3) — target ≥ 1.0
4. **Investment Diversification Score** (0–10): one point each for having: mutual funds, stocks, gold, FD/RD, PPF/EPF, real estate, crypto (capped at 7), plus 3 bonus for covering equity + debt + alternate

Flag risks clearly:
- `over_leveraged`: if EMIs > 40% of monthly income
- `under_invested`: if all liquid money sits in savings with no market exposure
- `poor_diversification`: if score < 3
- `no_emergency_fund`: if liquidity ratio < 1.0

Output format:
```
FINANCIAL HEALTH — [Name] | [Date]
Net Worth:              ₹[amount]
Monthly Surplus:        ₹[amount]
Liquidity Ratio:        [ratio] ([status])
Diversification Score:  [score]/10
Flags: [list or "None"]
```

---

## B. Joint Investment Opportunity Analysis

When any resident asks about investing together or pooling money:

```bash
python skills/devlithium-invest/scripts/invest_advisor.py --action joint_opportunity
```

Steps:
1. Load `financial.liquidity` and `venture_interests.capital_available_for_ventures_inr` from all 3 profiles
2. Identify shared risk appetite — use the **lowest** as baseline (conservative > moderate > aggressive)
3. Calculate `combined_investable_capital` = sum of all `capital_available_for_ventures_inr`
4. Recommend top 3 joint options based on capital + Jaipur context:

| Option | Min Capital | Risk | Notes |
|--------|-------------|------|-------|
| Real estate (plot/flat) | ₹25L | Low-Medium | Best for Jaipur — see Section D |
| Liquid mutual funds | ₹50K | Low | Pool for emergency + returns |
| Gold ETF | ₹10K | Low | Inflation hedge; easy to exit |
| Fixed income (FD/bonds) | ₹25K | Very Low | If risk appetite is conservative |
| Joint SIP (equity) | ₹5K/mo | Medium-High | If risk appetite is moderate+ |

Output the top 3 with: option name, capital needed, expected return range, rationale.

---

## C. Goal-Based Recommendation Engine

For each financial goal in each resident's `goals.financial[]`:

```bash
python skills/devlithium-invest/scripts/invest_advisor.py --action goal_gap --user u3
```

For each goal:
- `monthly_savings_needed` = (target_inr − current_saved_inr) / months_remaining
- `current_monthly_contribution` = from goal data (default 0 if not set)
- `gap` = monthly_savings_needed − current_monthly_contribution
- If gap > 0: flag as shortfall

Output example:
```
GOAL GAP ANALYSIS — Hanu
Goal: Buy a House
  Target:              ₹30,00,000 by Jan 2030
  Monthly needed:      ₹8,200
  Currently saving:    ₹5,000
  Shortfall:           ₹3,200/month
  Recommend:           SIP top-up ₹2,000 + reduce discretionary spend ₹1,200
```

Recommendations priority:
1. SIP top-up (if equity exposure is low)
2. Expense reduction (if surplus > ₹3,000)
3. Timeline extension (if neither is feasible)

---

## D. Net Worth Snapshot

```bash
python skills/devlithium-invest/scripts/invest_advisor.py --action net_worth --user all
```

Quick summary table:
```
NET WORTH SNAPSHOT — [Date]
Resident   | Net Worth   | Liquid     | Risk        | Investable
-----------|-------------|------------|-------------|------------
Dev (u1)   | ₹X          | ₹X         | Moderate    | ₹X
Sunil (u2) | ₹X          | ₹X         | [level]     | ₹X
Hanu (u3)  | ₹X          | ₹X         | [level]     | ₹X
COMBINED   | ₹X          | ₹X         | Conservative| ₹X
```

---

## E. Scenario Planning

When user says "what if I invest ₹X in Y":

```bash
python skills/devlithium-invest/scripts/invest_advisor.py --action joint_opportunity --capital 500000
```

Model simple compounding scenarios:
- 1-year, 3-year, 5-year projected value at assumed CAGR (6%, 10%, 14%)
- Compare to keeping in savings (4% average)

---

## F. Jaipur Real Estate Intelligence (Embedded Knowledge)

Use this as baseline when any resident asks about property investment in Jaipur:

**Prime areas and avg price/sqft (2026 estimates):**
| Area | Price/sqft | Character |
|------|-----------|-----------|
| C-Scheme | ₹8,000–12,000 | Premium; best appreciation |
| Vaishali Nagar | ₹5,000–7,000 | Established; family-friendly |
| Mansarovar | ₹4,500–6,500 | Good connectivity; growing |
| Jagatpura | ₹3,500–5,000 | Airport proximity; fast growth |
| Ajmer Road | ₹3,000–4,500 | Affordable; long-term play |
| Sitapura | ₹3,000–4,000 | Industrial belt; rental demand |

**Plots (100–200 sqyd) price ranges:**
- Jagatpura: ₹15L–25L for 100 sqyd
- Ajmer Road (outer): ₹12L–20L for 100 sqyd
- Mansarovar Extension: ₹20L–35L for 100 sqyd

**Key rules:**
- Always verify RERA registration before recommending any builder flat
- Plots in JDA/Nagar Nigam areas have better resale than private layouts
- Avoid agricultural land conversion deals — legal risk is high
- Minimum combined capital for entry-level plot: ₹12L; for flat: ₹25L

---

## Rules
- Never recommend a product without stating its risk level
- Always compare to the alternative of doing nothing (opportunity cost)
- If a resident is over-leveraged, recommend debt reduction before new investments
- Flag tax implications: LTCG on equity (>1yr, >₹1L), STCG (15%), real estate indexation
- Joint investment decisions require approval from all participating residents
