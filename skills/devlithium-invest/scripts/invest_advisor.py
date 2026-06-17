"""
devlithium-invest: invest_advisor.py
Financial analysis, investment recommendations, and wealth tracking for Devlithium residents.
Usage:
  python invest_advisor.py --action health_check --user u1
  python invest_advisor.py --action joint_opportunity
  python invest_advisor.py --action goal_gap --user u3
  python invest_advisor.py --action net_worth --user all
  python invest_advisor.py --action joint_opportunity --capital 500000
"""
import json
import argparse
import os
from datetime import date, datetime

PROFILES_DIR = os.path.join(os.path.dirname(__file__), "../../../data/profiles")
USERS = ["u1", "u2", "u3"]
USER_NAMES = {"u1": "Dev", "u2": "Sunil", "u3": "Hanu"}


def load_profile(uid):
    path = os.path.join(PROFILES_DIR, f"{uid}.json")
    if not os.path.exists(path):
        return None
    with open(path) as f:
        return json.load(f)


def calc_net_worth(financial):
    assets = financial.get("assets", {})
    liabilities = financial.get("liabilities", {})

    # Assets
    n = lambda v: v or 0  # null-safe helper

    re_value = sum(
        n(p.get("estimated_value_inr", 0))
        for p in assets.get("real_estate", [])
    )
    vehicle_value = sum(
        n(v.get("estimated_value_inr", 0))
        for v in assets.get("vehicles", [])
    )
    investments = assets.get("investments", {})
    mf_value = sum(
        n(m.get("current_value_inr", 0))
        for m in investments.get("mutual_funds", [])
    )
    stock_value = sum(
        n(s.get("current_value_inr", 0))
        for s in investments.get("stocks", [])
    )
    # also count bonds if present
    bond_value = sum(
        n(b.get("current_value_inr", 0))
        for b in investments.get("bonds", [])
    )
    fd_value = sum(
        n(fd.get("amount_inr", 0))
        for fd in investments.get("fd_rd", [])
    )
    gold_value = n(investments.get("gold", {}).get("estimated_value_inr", 0))
    crypto_value = sum(
        n(c.get("current_value_inr", 0))
        for c in investments.get("crypto", [])
    )
    ppf_epf = investments.get("ppf_epf", {})
    ppf_value = n(ppf_epf.get("ppf_balance_inr", 0)) + n(ppf_epf.get("epf_balance_inr", 0))
    # deployable corpus (e.g. Sunil's parents' money)
    corpus_value = n(investments.get("deployable_corpus", {}).get("amount_inr", 0))
    liquidity = financial.get("liquidity", {})
    liquid_total = n(liquidity.get("total_liquid_inr", 0)) or (
        n(liquidity.get("savings_account_inr", 0))
        + n(liquidity.get("current_account_inr", 0))
        + n(liquidity.get("cash_in_hand_inr", 0))
        + n(liquidity.get("liquid_mf_inr", 0))
    )

    total_assets = (
        re_value + vehicle_value + mf_value + stock_value + bond_value
        + fd_value + gold_value + crypto_value + ppf_value + corpus_value + liquid_total
    )

    # Liabilities
    home_loan = n(liabilities.get("home_loan", {}).get("outstanding_inr", 0))
    vehicle_loan = n(liabilities.get("vehicle_loan", {}).get("outstanding_inr", 0))
    personal_loans = sum(
        n(l.get("outstanding_inr", 0))
        for l in liabilities.get("personal_loans", [])
    )
    cc_due = sum(
        n(c.get("outstanding_inr", 0))
        for c in liabilities.get("credit_cards", [])
    )
    total_liabilities = home_loan + vehicle_loan + personal_loans + cc_due

    return total_assets - total_liabilities, total_assets, total_liabilities


def calc_monthly_emis(liabilities):
    n = lambda v: v or 0
    emi = 0
    emi += n(liabilities.get("home_loan", {}).get("emi_inr", 0))
    emi += n(liabilities.get("vehicle_loan", {}).get("emi_inr", 0))
    emi += sum(n(l.get("emi_inr", 0)) for l in liabilities.get("personal_loans", []))
    emi += sum(n(c.get("min_payment_inr", 0)) for c in liabilities.get("credit_cards", []))
    return emi


def calc_diversification_score(investments):
    n = lambda v: v or 0
    score = 0
    if investments.get("mutual_funds"):
        score += 1
    if investments.get("stocks"):
        score += 1
    if n(investments.get("gold", {}).get("estimated_value_inr", 0)) > 0:
        score += 1
    if investments.get("bonds"):
        score += 1
    if investments.get("fd_rd"):
        score += 1
    ppf_epf = investments.get("ppf_epf", {})
    if n(ppf_epf.get("ppf_balance_inr", 0)) > 0 or n(ppf_epf.get("epf_balance_inr", 0)) > 0:
        score += 1
    if investments.get("crypto"):
        score += 1
    has_equity = bool(investments.get("mutual_funds") or investments.get("stocks"))
    has_debt = bool(investments.get("fd_rd") or investments.get("bonds") or n(ppf_epf.get("ppf_balance_inr", 0)) > 0)
    has_alt = bool(n(investments.get("gold", {}).get("estimated_value_inr", 0)) > 0 or investments.get("crypto"))
    if has_equity:
        score += 1
    if has_debt:
        score += 1
    if has_alt:
        score += 1
    return min(score, 10)


def health_check(uid):
    profile = load_profile(uid)
    if not profile:
        print(f"Profile not found for {uid}")
        return

    name = profile["_meta"]["name"]
    financial = profile.get("financial", {})
    income = financial.get("monthly_income", {}).get("total_inr", 0) or 0
    liabilities = financial.get("liabilities", {})
    investments = financial.get("assets", {}).get("investments", {})
    liquidity = financial.get("liquidity", {})

    emis = calc_monthly_emis(liabilities)
    # Min floor: ₹12k/month for single person in Jaipur (food, transport, misc)
    estimated_monthly_expenses = max(income * 0.4, 12000)
    surplus = income - emis - estimated_monthly_expenses

    net_worth, total_assets, total_liabilities = calc_net_worth(financial)

    nn = lambda v: v or 0
    liquid_total = nn(liquidity.get("total_liquid_inr", 0)) or (
        nn(liquidity.get("savings_account_inr", 0))
        + nn(liquidity.get("current_account_inr", 0))
        + nn(liquidity.get("cash_in_hand_inr", 0))
        + nn(liquidity.get("liquid_mf_inr", 0))
    )
    emergency_fund_needed = estimated_monthly_expenses * 3
    liquidity_ratio = round(liquid_total / emergency_fund_needed, 2) if emergency_fund_needed > 0 else 0.0

    div_score = calc_diversification_score(investments)

    # --- Gap 1: Cash flow runway ---
    monthly_burn = abs(surplus) if surplus < 0 else 0
    runway_months = round(liquid_total / monthly_burn, 1) if monthly_burn > 0 else None

    # --- Gap 2: EMI-with-unknown-principal detection ---
    unknown_principal_loans = [
        l for l in liabilities.get("personal_loans", [])
        if (l.get("emi_inr") or 0) > 0 and not (l.get("outstanding_inr") or 0)
    ]

    # --- Flags ---
    flags = []
    if surplus < 0:
        flags.append(f"CRITICAL: negative_cash_flow (burning INR {monthly_burn:,.0f}/month)")
    if income > 0 and emis > income * 0.4:
        flags.append("over_leveraged (EMIs > 40% income)")
    if div_score < 3:
        flags.append("poor_diversification (score < 3)")
    if liquidity_ratio < 1.0:
        flags.append("no_emergency_fund (liquidity ratio < 1.0)")
    if income > 0 and not investments.get("mutual_funds") and not investments.get("stocks"):
        flags.append("under_invested (no market exposure)")
    if unknown_principal_loans:
        flags.append(f"data_gap: {len(unknown_principal_loans)} loan(s) have EMI but no outstanding principal recorded")

    risk = financial.get("risk_appetite", "unknown")

    # --- Recommendations ---
    recs = []
    if surplus < 0 and runway_months:
        recs.append(f"URGENT — Liquidity runs out in ~{runway_months} months. Generate active income or liquidate a low-priority asset.")
    if unknown_principal_loans:
        recs.append("Update profile with loan outstanding amounts so net worth and liability ratio are accurate.")
    if div_score >= 4 and risk == "aggressive" and not investments.get("mutual_funds"):
        recs.append("Add equity mutual fund SIP (even INR 1K/month) to build systematic wealth alongside lump-sum portfolio.")
    if surplus >= 0 and surplus < 5000:
        recs.append("Thin surplus — avoid new EMIs. Build surplus to INR 5K+/month before any new commitment.")
    if not recs:
        recs.append("Profile healthy — continue current allocation.")

    lr_status = "Good" if liquidity_ratio >= 1.0 else "LOW — build emergency fund"

    print(f"\nFINANCIAL HEALTH — {name} ({uid}) | {date.today()}")
    print("=" * 57)
    print(f"Monthly Income:         INR {income:>12,.0f}")
    print(f"Monthly EMIs:           INR {emis:>12,.0f}")
    print(f"Est. Monthly Expenses:  INR {estimated_monthly_expenses:>12,.0f}")
    print(f"Monthly Surplus:        INR {surplus:>12,.0f}")
    print(f"Total Assets:           INR {total_assets:>12,.0f}")
    print(f"Total Liabilities:      INR {total_liabilities:>12,.0f}")
    print(f"Net Worth:              INR {net_worth:>12,.0f}")
    print(f"Liquid Funds:           INR {liquid_total:>12,.0f}")
    if runway_months:
        print(f"Cash Flow Runway:       {runway_months} months  ({'OK' if runway_months > 6 else 'WARNING' if runway_months > 3 else 'CRITICAL'})")
    print(f"Liquidity Ratio:        {liquidity_ratio:<6} ({lr_status})")
    print(f"Diversification Score:  {div_score}/10")
    print(f"Risk Appetite:          {risk.capitalize()}")
    print()
    print("FLAGS:")
    for f in flags:
        prefix = "  [!!]" if "CRITICAL" in f or "data_gap" in f else "  [!] "
        print(f"{prefix} {f}")
    if not flags:
        print("  None")
    print()
    print("RECOMMENDATIONS:")
    for i, r in enumerate(recs, 1):
        print(f"  {i}. {r}")
    print()


def joint_opportunity(capital_override=None):
    combined_capital = 0
    risk_levels = []
    risk_rank = {"conservative": 1, "moderate": 2, "aggressive": 3}
    names = []

    print(f"\nJOINT INVESTMENT OPPORTUNITY ANALYSIS — {date.today()}")
    print("=" * 60)

    for uid in USERS:
        profile = load_profile(uid)
        if not profile:
            print(f"  [{uid}] Profile not found — skipping.")
            continue
        name = profile["_meta"]["name"]
        names.append(name)
        venture = profile.get("venture_interests", {})
        cap = venture.get("capital_available_for_ventures_inr", 0) or 0
        combined_capital += cap
        risk = profile.get("financial", {}).get("risk_appetite", "conservative")
        risk_levels.append(risk)
        print(f"  {name} ({uid}): Investable = INR {cap:,.0f} | Risk = {risk.capitalize()}")

    if capital_override:
        combined_capital = capital_override
        print(f"\n  [Scenario override] Using capital: INR {capital_override:,.0f}")

    # Lowest risk = baseline
    baseline_risk = min(risk_levels, key=lambda r: risk_rank.get(r, 2)) if risk_levels else "conservative"
    print(f"\nCombined Investable Capital: INR {combined_capital:,.0f}")
    print(f"Baseline Risk (lowest):      {baseline_risk.capitalize()}")
    print()

    # Build recommendations
    options = []
    if combined_capital >= 2500000:
        options.append((
            "1. Real Estate — Plot/Flat in Jaipur",
            "INR 25L+",
            "8–12% CAGR (appreciation + rental)",
            "Best long-term hedge. Plots in Jagatpura/Ajmer Road (INR 12L–25L for 100 sqyd). "
            "Flats in Mansarovar/Vaishali Nagar INR 25L–50L. Needs JDA verification."
        ))
    if combined_capital >= 50000 and baseline_risk in ("moderate", "conservative"):
        options.append((
            "2. Liquid Mutual Fund (Pool)",
            "INR 50K+",
            "5–7% p.a. (redeemable anytime)",
            "Low risk. Pool together in one folio. Acts as house emergency + growth fund. "
            "Recommended: Parag Parikh Liquid / HDFC Liquid."
        ))
    if combined_capital >= 10000:
        options.append((
            "3. Gold ETF (Inflation Hedge)",
            "INR 10K+",
            "6–9% p.a.",
            "Low risk. Protects against INR depreciation. Can start with 1 unit (~INR 5K–6K). "
            "Split equally across 3 accounts or one joint SGB."
        ))
    if baseline_risk == "conservative" and combined_capital >= 25000:
        options.append((
            "4. Fixed Deposit / RBI Bonds",
            "INR 25K+",
            "6.5–7.5% p.a.",
            "Safest option. Pool in one high-yield FD (SBI/HDFC). Lock-in 1–3 years. "
            "RBI Floating Rate Bonds at 8.05% are ideal."
        ))
    if baseline_risk == "aggressive" and combined_capital >= 5000:
        options.append((
            "5. Joint SIP — Equity Mutual Fund",
            "INR 5K/month+",
            "10–15% CAGR (5yr avg)",
            "Medium-high risk. Each contributes INR 2K–3K/month. "
            "Recommended: Mirae Asset Large Cap + Parag Parikh Flexi Cap."
        ))

    if not options:
        print("Insufficient capital for joint investment at this time.")
        print(f"Min recommended: INR 10,000. Current: INR {combined_capital:,.0f}")
        return

    # Show top 3
    print("TOP JOINT INVESTMENT OPTIONS:")
    print("-" * 60)
    for opt in options[:3]:
        title, min_cap, returns, notes = opt
        print(f"\n{title}")
        print(f"  Min Capital:  {min_cap}")
        print(f"  Expected:     {returns}")
        print(f"  Notes:        {notes}")

    # Scenario compounding
    if combined_capital > 0:
        print(f"\nSCENARIO: INR {combined_capital:,.0f} invested today")
        print(f"{'Horizon':<10} {'@6% (FD)':<18} {'@10% (Equity)':<20} {'@14% (Aggressive)'}")
        print("-" * 65)
        for years in [1, 3, 5]:
            v6 = combined_capital * (1.06 ** years)
            v10 = combined_capital * (1.10 ** years)
            v14 = combined_capital * (1.14 ** years)
            print(f"{years}yr{'':<7} INR {v6:>10,.0f}    INR {v10:>10,.0f}    INR {v14:>10,.0f}")
    print()


def goal_gap(uid):
    profile = load_profile(uid)
    if not profile:
        print(f"Profile not found for {uid}")
        return

    name = profile["_meta"]["name"]
    goals = profile.get("goals", {}).get("financial", [])

    print(f"\nGOAL GAP ANALYSIS — {name} ({uid}) | {date.today()}")
    print("=" * 55)

    if not goals:
        print("No financial goals recorded in profile.")
        print("Add goals to data/profiles/{uid}.json under goals.financial[]")
        return

    today = date.today()
    for goal in goals:
        title = goal.get("title", "Unnamed Goal")
        target = goal.get("target_inr", 0) or 0
        saved = goal.get("current_saved_inr", 0) or 0
        contribution = goal.get("monthly_contribution_inr", 0) or 0
        deadline_str = goal.get("target_date", None)

        remaining = max(0, target - saved)
        if deadline_str:
            try:
                deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
                months_remaining = max(
                    1,
                    (deadline.year - today.year) * 12 + (deadline.month - today.month)
                )
            except ValueError:
                months_remaining = 60  # default 5 years
        else:
            months_remaining = 60

        monthly_needed = remaining / months_remaining if months_remaining > 0 else remaining
        gap = monthly_needed - contribution

        print(f"\nGoal: {title}")
        print(f"  Target:           INR {target:,.0f}" + (f" by {deadline_str}" if deadline_str else ""))
        print(f"  Current Saved:    INR {saved:,.0f}")
        print(f"  Remaining:        INR {remaining:,.0f}")
        print(f"  Months Left:      {months_remaining}")
        print(f"  Monthly Needed:   INR {monthly_needed:,.0f}")
        print(f"  Currently Saving: INR {contribution:,.0f}")

        if gap > 0:
            print(f"  Shortfall:        INR {gap:,.0f}/month")
            # Recommend
            if gap <= 2000:
                print(f"  Recommend:        SIP top-up by INR {gap:,.0f}/month")
            elif gap <= 5000:
                sip_part = round(gap * 0.6)
                expense_part = round(gap * 0.4)
                print(f"  Recommend:        SIP top-up INR {sip_part:,.0f} + reduce discretionary INR {expense_part:,.0f}")
            else:
                print(f"  Recommend:        Review timeline OR significantly increase income/cut expenses")
                extended = int(remaining / max(contribution, 1))
                print(f"  Alt:              At current INR {contribution:,.0f}/month, goal achieved in {extended} months")
        else:
            surplus = abs(gap)
            print(f"  Status:           ON TRACK (surplus INR {surplus:,.0f}/month)")

    print()


def net_worth_all(uid):
    if uid == "all":
        targets = USERS
    else:
        targets = [uid]

    print(f"\nNET WORTH SNAPSHOT — {date.today()}")
    print("=" * 70)
    print(f"{'Resident':<14} {'Net Worth':>14} {'Liquid':>12} {'Risk':>14} {'Investable':>12}")
    print("-" * 70)

    combined_nw = 0
    combined_liquid = 0
    combined_investable = 0
    all_risks = []

    for t in targets:
        profile = load_profile(t)
        if not profile:
            print(f"{USER_NAMES.get(t, t):<14} {'N/A':>14} {'N/A':>12} {'N/A':>14} {'N/A':>12}")
            continue

        name = profile["_meta"]["name"]
        financial = profile.get("financial", {})
        nw, _, _ = calc_net_worth(financial)
        liquidity = financial.get("liquidity", {})
        liquid = liquidity.get("total_liquid_inr", 0) or (
            liquidity.get("savings_account_inr", 0)
            + liquidity.get("current_account_inr", 0)
            + liquidity.get("cash_in_hand_inr", 0)
            + liquidity.get("liquid_mf_inr", 0)
        )
        risk = financial.get("risk_appetite", "unknown")
        investable = profile.get("venture_interests", {}).get("capital_available_for_ventures_inr", 0) or 0

        combined_nw += nw
        combined_liquid += liquid
        combined_investable += investable
        all_risks.append(risk)

        print(f"{name} ({t}){'':>4} INR {nw:>10,.0f}  INR {liquid:>8,.0f}  {risk.capitalize():>14}  INR {investable:>8,.0f}")

    if len(targets) > 1:
        risk_rank = {"conservative": 1, "moderate": 2, "aggressive": 3}
        baseline = min(all_risks, key=lambda r: risk_rank.get(r, 2)) if all_risks else "unknown"
        print("-" * 70)
        print(f"{'COMBINED':<14} INR {combined_nw:>10,.0f}  INR {combined_liquid:>8,.0f}  {baseline.capitalize():>14}  INR {combined_investable:>8,.0f}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Devlithium Investment Advisor"
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["health_check", "joint_opportunity", "goal_gap", "net_worth"],
        help="Action to perform"
    )
    parser.add_argument(
        "--user",
        default="all",
        help="User ID: u1, u2, u3, or all"
    )
    parser.add_argument(
        "--capital",
        type=float,
        default=None,
        help="Optional capital override for scenario planning (INR)"
    )
    args = parser.parse_args()

    if args.action == "health_check":
        if args.user == "all":
            for uid in USERS:
                health_check(uid)
        else:
            health_check(args.user)

    elif args.action == "joint_opportunity":
        joint_opportunity(capital_override=args.capital)

    elif args.action == "goal_gap":
        if args.user == "all":
            for uid in USERS:
                goal_gap(uid)
        else:
            goal_gap(args.user)

    elif args.action == "net_worth":
        net_worth_all(args.user)


if __name__ == "__main__":
    main()
