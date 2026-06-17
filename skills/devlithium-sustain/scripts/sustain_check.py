"""
devlithium-sustain: sustain_check.py
Sustainability analysis: terrace farm, rental income, solar ROI, weekly pulse.
Usage:
  --action terrace       --crop "Tomato" --planted_date 2026-05-01 \
                         --harvest_date 2026-07-01 --yield_kg 5 --market_price 40
  --action rental        (assess all rental opportunities)
  --action solar         [--monthly_bill 1500]
  --action weekly_pulse  (Monday pulse report)
"""
import json
import argparse
import os
import sys
from datetime import date, datetime

KB_PATH = os.path.join(os.path.dirname(__file__), "../../../data/house_kb.json")


def load_kb():
    with open(KB_PATH) as f:
        return json.load(f)


def save_kb(kb):
    kb["_meta"]["last_updated"] = str(date.today())
    with open(KB_PATH, "w") as f:
        json.dump(kb, f, indent=2)


def days_until(date_str):
    """Return days until a date string (YYYY-MM-DD). Negative = past."""
    try:
        target = datetime.strptime(date_str, "%Y-%m-%d").date()
        return (target - date.today()).days
    except (ValueError, TypeError):
        return None


def action_terrace(kb, args):
    """Add or list terrace farm crops."""
    sustain = kb.setdefault("sustainability", {})
    farm = sustain.setdefault("terrace_farm", {
        "active": False,
        "crops": [],
        "estimated_monthly_savings_inr": 0,
    })
    crops = farm.setdefault("crops", [])

    # If adding a new crop
    if args.crop:
        if not args.planted_date or not args.harvest_date or args.yield_kg is None or args.market_price is None:
            print("ERROR: --crop requires --planted_date, --harvest_date, --yield_kg, --market_price")
            sys.exit(1)

        savings = round(float(args.yield_kg) * float(args.market_price), 2)
        crop = {
            "name": args.crop,
            "planted_date": args.planted_date,
            "expected_harvest_date": args.harvest_date,
            "yield_kg": float(args.yield_kg),
            "market_price_per_kg_inr": float(args.market_price),
            "estimated_savings_inr": savings,
            "status": "growing",
        }
        crops.append(crop)
        farm["active"] = True

        # Recalculate monthly savings estimate
        growing = [c for c in crops if c.get("status") == "growing"]
        if growing:
            # Spread savings across crop durations
            total_monthly = 0
            for c in growing:
                d = days_until(c["expected_harvest_date"])
                months_left = max((d or 30) / 30, 1)
                total_monthly += c["estimated_savings_inr"] / months_left
            farm["estimated_monthly_savings_inr"] = round(total_monthly, 0)

        save_kb(kb)
        print(f"\n🌱 CROP ADDED — {args.crop}")
        print(f"{'='*45}")
        print(f"Planted:        {args.planted_date}")
        print(f"Harvest date:   {args.harvest_date}")
        print(f"Expected yield: {args.yield_kg} kg @ ₹{args.market_price}/kg")
        print(f"Est. savings:   ₹{savings:,.0f}")
        print()

    # Always show farm status
    print(f"\n🌱 TERRACE FARM STATUS — {date.today()}")
    print(f"{'='*45}")
    if not crops:
        print("  No crops tracked yet.")
        print("\n  💡 Recommended for Jaipur (May):")
        print("     Chilli → ₹60–100/kg | harvest in ~90 days")
        print("     Bottle Gourd → ₹20–40/kg | harvest in ~60 days")
    else:
        growing = sorted(
            [c for c in crops if c.get("status") != "harvested"],
            key=lambda c: days_until(c.get("expected_harvest_date", "2099-01-01")) or 9999,
        )
        print(f"Active crops: {len(growing)}")
        for c in growing:
            d = days_until(c.get("expected_harvest_date"))
            alert = "  ⏰ Harvest soon!" if d is not None and d <= 14 else ""
            d_str = f"{d} days" if d is not None else "?"
            print(f"  {c['name']:<15} → Harvest: {c.get('expected_harvest_date', '?')} ({d_str})   "
                  f"Est. savings: ₹{c['estimated_savings_inr']:,.0f}{alert}")

    monthly = farm.get("estimated_monthly_savings_inr", 0)
    print(f"\nMonthly savings estimate: ₹{monthly:,.0f}")
    print()


def action_rental(kb, args):
    """Assess rental income opportunities for the house."""
    sustain = kb.setdefault("sustainability", {})
    rental = sustain.setdefault("rental_potential", {
        "assessed": False,
        "rentable_areas": [],
        "estimated_monthly_income_inr": 0,
    })

    features = kb.get("house", {}).get("features", {})
    has_terrace = features.get("has_terrace", False)
    has_parking = features.get("parking", False)
    active_residents = [r for r in kb.get("residents", []) if r.get("status") == "active"]
    max_rooms = len([r for r in kb.get("rooms", []) if r.get("type") == "bedroom"])
    occupied_rooms = len(active_residents)

    opportunities = []

    # Terrace events
    if has_terrace:
        terrace_event = {
            "type": "terrace_events",
            "description": "Terrace rental for events (birthday, pre-wedding, gatherings)",
            "upfront_cost_inr": 5000,
            "monthly_income_conservative_inr": 4000,
            "monthly_income_optimistic_inr": 12000,
            "payback_months": 2,
            "notes": "2–3 events/month @ ₹2,000–5,000 per event. Needs basic setup: cleaning, lighting, seating.",
        }
        opportunities.append(terrace_event)

    # Parking
    if not has_parking:
        # Check if there's potential for street/common parking
        parking = {
            "type": "parking_rental",
            "description": "Dedicated parking spot rental (if space available)",
            "upfront_cost_inr": 0,
            "monthly_income_conservative_inr": 500,
            "monthly_income_optimistic_inr": 1500,
            "payback_months": 0,
            "notes": "Assess available ground-level space. Low effort, passive income.",
        }
        opportunities.append(parking)

    # Telecom tower (terrace, top floor)
    if has_terrace:
        tower = {
            "type": "telecom_tower_lease",
            "description": "Telecom tower lease on terrace (Jio/Airtel/Vi)",
            "upfront_cost_inr": 10000,
            "monthly_income_conservative_inr": 5000,
            "monthly_income_optimistic_inr": 15000,
            "payback_months": 2,
            "notes": "Top-floor terrace ideal. Long-term 10–15 yr lease. Requires structural assessment & owner consent.",
        }
        opportunities.append(tower)

    # Spare room PG
    if occupied_rooms < max_rooms:
        spare = max_rooms - occupied_rooms
        spare_room = {
            "type": "spare_room_pg",
            "description": f"Spare bedroom(s) as PG accommodation ({spare} room(s) available)",
            "upfront_cost_inr": 3000,
            "monthly_income_conservative_inr": 4000 * spare,
            "monthly_income_optimistic_inr": 8000 * spare,
            "payback_months": 1,
            "notes": f"PG in Jaipur 302021: ₹4,000–8,000/room/month. Requires Dev approval (new person gate).",
        }
        opportunities.append(spare_room)

    rental["assessed"] = True
    rental["rentable_areas"] = opportunities
    total_conservative = sum(o["monthly_income_conservative_inr"] for o in opportunities)
    total_optimistic = sum(o["monthly_income_optimistic_inr"] for o in opportunities)
    rental["estimated_monthly_income_inr"] = total_conservative
    save_kb(kb)

    print(f"\n🏠 RENTAL INCOME ASSESSMENT — {date.today()}")
    print(f"{'='*55}")
    print(f"House: {kb.get('house', {}).get('name', 'Devlithium House')}, Jaipur")
    print()

    opportunities_sorted = sorted(opportunities,
                                  key=lambda o: o["monthly_income_conservative_inr"], reverse=True)
    for i, opp in enumerate(opportunities_sorted, 1):
        roi_label = "HIGH VALUE" if opp["monthly_income_conservative_inr"] >= 4000 else \
                    "MEDIUM VALUE" if opp["monthly_income_conservative_inr"] >= 1000 else "LOW VALUE"
        annual = opp["monthly_income_conservative_inr"] * 12 - opp["upfront_cost_inr"]
        print(f"  {i}. {opp['description']}")
        print(f"     Upfront cost:    ₹{opp['upfront_cost_inr']:,.0f}")
        print(f"     Monthly income:  ₹{opp['monthly_income_conservative_inr']:,.0f} – ₹{opp['monthly_income_optimistic_inr']:,.0f}")
        print(f"     Payback:         {opp['payback_months']} month(s)")
        print(f"     Net annual:      ₹{annual:,.0f}")
        print(f"     Verdict:         {roi_label}")
        print(f"     Note: {opp['notes']}")
        print()

    print(f"{'='*55}")
    print(f"Total monthly potential:")
    print(f"  Conservative: ₹{total_conservative:,.0f}")
    print(f"  Optimistic:   ₹{total_optimistic:,.0f}")
    print()

    best = opportunities_sorted[0] if opportunities_sorted else None
    if best:
        print(f"Top recommendation: {best['description']}")
        print(f"  → Potential ₹{best['monthly_income_conservative_inr']:,.0f}+/month")
        if best["upfront_cost_inr"] > 500:
            print(f"  ⚡ Requires Dev approval (upfront cost > ₹500)")
    print()


def action_solar(kb, args):
    """Model solar panel ROI for Jaipur rooftop."""
    sustain = kb.setdefault("sustainability", {})
    energy = sustain.setdefault("energy", {
        "solar_assessed": False,
        "monthly_bill_avg_inr": 0,
    })

    features = kb.get("house", {}).get("features", {})
    has_solar = features.get("solar_panels", False)

    if args.monthly_bill is not None:
        energy["monthly_bill_avg_inr"] = float(args.monthly_bill)

    monthly_bill = energy.get("monthly_bill_avg_inr", 0)

    # Jaipur-specific solar constants
    INSTALL_COST_2KW = 180000  # ₹1,80,000 median
    MNRE_SUBSIDY_PCT = 0.40    # 40% subsidy on first 2kW
    SUBSIDY_CAP = 72000        # ₹72,000 max subsidy
    subsidy = min(INSTALL_COST_2KW * MNRE_SUBSIDY_PCT, SUBSIDY_CAP)
    net_cost = INSTALL_COST_2KW - subsidy

    MONTHLY_SAVINGS_CONSERVATIVE = 1500
    MONTHLY_SAVINGS_OPTIMISTIC = 2500
    MONTHLY_SAVINGS_AVG = 2000
    SYSTEM_LIFE_YEARS = 25

    payback_months_conservative = net_cost / MONTHLY_SAVINGS_CONSERVATIVE
    payback_months_avg = net_cost / MONTHLY_SAVINGS_AVG
    total_savings_25yr = (MONTHLY_SAVINGS_AVG * 12 * SYSTEM_LIFE_YEARS) - net_cost

    energy["solar_assessed"] = True
    save_kb(kb)

    print(f"\n☀️ SOLAR ASSESSMENT — Devlithium House, Jaipur")
    print(f"{'='*52}")
    print(f"Current solar panels:  {'YES' if has_solar else 'NO'}")
    if monthly_bill > 0:
        print(f"Current monthly bill:  ₹{monthly_bill:,.0f}")
    print()

    if has_solar:
        print("Solar panels already installed.")
        if monthly_bill > 0:
            print(f"Track actual savings vs. ₹{monthly_bill:,.0f} baseline in energy.monthly_bill_avg_inr.")
    else:
        print(f"Recommended system:    2kW Rooftop Photovoltaic")
        print(f"Install cost:          ₹{INSTALL_COST_2KW:,.0f}")
        print(f"MNRE subsidy (40%):   -₹{subsidy:,.0f}")
        print(f"Net cost to you:       ₹{net_cost:,.0f}")
        print()
        print(f"Monthly generation:    ~240–300 units (kWh)")
        print(f"Monthly savings:       ₹{MONTHLY_SAVINGS_CONSERVATIVE:,.0f} – ₹{MONTHLY_SAVINGS_OPTIMISTIC:,.0f}")
        print()
        print(f"Payback period:")
        print(f"  Conservative:        {payback_months_conservative/12:.1f} years")
        print(f"  Average:             {payback_months_avg/12:.1f} years")
        print(f"Net gain over 25yr:    ₹{total_savings_25yr:,.0f}")
        print()

        if monthly_bill > 0:
            coverage_pct = min((MONTHLY_SAVINGS_AVG / monthly_bill) * 100, 100)
            print(f"Bill coverage:         ~{coverage_pct:.0f}% of your ₹{monthly_bill:,.0f} bill")
            print()

        print(f"Recommendation:        HIGH ROI — strong solar zone (6.5 peak sun hrs/day)")
        print(f"\nNext steps:")
        print(f"  1. Submit MNRE subsidy application before getting quotes")
        print(f"     (subsidy reduces cost by ₹{subsidy:,.0f})")
        print(f"  2. Get 2 vendor quotes: Tata Solar, Loom Solar (both service Jaipur)")
        print(f"  3. Seek Dev's approval before any installation (physical change gate)")
    print()


def action_weekly_pulse(kb, args):
    """Weekly sustainability pulse — called by devlithium-daily on Mondays."""
    today = date.today()
    sustain = kb.get("sustainability", {})
    farm = sustain.get("terrace_farm", {})
    rental = sustain.get("rental_potential", {})
    energy = sustain.get("energy", {})

    crops = farm.get("crops", [])
    active_crops = [c for c in crops if c.get("status") == "growing"]
    harvest_due = [c for c in active_crops
                   if (days_until(c.get("expected_harvest_date")) or 999) <= 14]

    monthly_farm_savings = farm.get("estimated_monthly_savings_inr", 0)
    rental_assessed = rental.get("assessed", False)
    rental_monthly = rental.get("estimated_monthly_income_inr", 0)
    solar_assessed = energy.get("solar_assessed", False)
    solar_installed = kb.get("house", {}).get("features", {}).get("solar_panels", False)

    # Calculate week savings (approximate: monthly / 4.3)
    weekly_farm_savings = round(monthly_farm_savings / 4.3, 0)

    print(f"\n🌿 SUSTAINABILITY PULSE — Week of {today}")
    print(f"{'='*50}")

    # Terrace Farm section
    print(f"\nTerrace Farm:")
    print(f"  Active crops:      {len(active_crops)}")
    if harvest_due:
        for c in harvest_due:
            d = days_until(c.get("expected_harvest_date"))
            print(f"  Harvest due:       {c['name']} ({d} days) ⏰")
    else:
        print(f"  Harvest due:       None in next 14 days")
    print(f"  Savings this week: ₹{weekly_farm_savings:,.0f} (estimate)")

    # Rental section
    print(f"\nRental Income:")
    if not rental_assessed:
        print(f"  Assessed:          NO  ← Run: python sustain_check.py --action rental")
    else:
        areas = rental.get("rentable_areas", [])
        print(f"  Opportunities:     {len(areas)} assessed")
        print(f"  Monthly potential: ₹{rental_monthly:,.0f} (conservative)")

    # Solar section
    print(f"\nSolar:")
    if solar_installed:
        print(f"  Status:            Installed ✓")
    elif not solar_assessed:
        print(f"  Assessed:          NO  ← Run: python sustain_check.py --action solar")
    else:
        print(f"  Assessed:          YES (not installed)")

    # Top recommendation
    recommendations = []

    if len(active_crops) == 0:
        recommendations.append((800, "Plant Coriander or Chilli batch now — quick ROI, harvest in 30–90 days"))
    if harvest_due:
        for c in harvest_due:
            recommendations.append((900, f"Harvest {c['name']} soon — collect ₹{c['estimated_savings_inr']:,.0f} savings"))
    if not rental_assessed:
        recommendations.append((700, "Run rental assessment to identify income opportunities"))
    elif rental_monthly > 0:
        best_area = max(rental.get("rentable_areas", [{}]),
                        key=lambda x: x.get("monthly_income_conservative_inr", 0), default={})
        if best_area:
            recommendations.append((600, f"Book {best_area.get('description', 'rental opportunity')} — potential ₹{best_area.get('monthly_income_conservative_inr', 0):,.0f}/month"))
    if not solar_assessed and not solar_installed:
        recommendations.append((500, "Assess solar ROI — top-floor Jaipur terrace is ideal, ₹1,500–2,500/month savings"))

    print(f"\nTop Recommendation:")
    if recommendations:
        recommendations.sort(reverse=True, key=lambda x: x[0])
        top = recommendations[0][1]
        print(f"  → {top}")
        if len(recommendations) > 1:
            print(f"\nAlso consider:")
            for _, rec in recommendations[1:3]:
                print(f"  • {rec}")
    else:
        print(f"  → House is optimized. Review in 1 week.")

    print(f"\n{'='*50}")
    print()


def main():
    parser = argparse.ArgumentParser(description="Devlithium Sustainability Manager")
    parser.add_argument("--action", required=True,
                        choices=["terrace", "rental", "solar", "weekly_pulse"])

    # Terrace args
    parser.add_argument("--crop", help="Crop name to add")
    parser.add_argument("--planted_date", help="Planted date (YYYY-MM-DD)")
    parser.add_argument("--harvest_date", help="Expected harvest date (YYYY-MM-DD)")
    parser.add_argument("--yield_kg", type=float, help="Expected yield in kg")
    parser.add_argument("--market_price", type=float, help="Market price per kg in INR")

    # Solar args
    parser.add_argument("--monthly_bill", type=float, help="Current monthly electricity bill in INR")

    args = parser.parse_args()
    kb = load_kb()

    actions = {
        "terrace": action_terrace,
        "rental": action_rental,
        "solar": action_solar,
        "weekly_pulse": action_weekly_pulse,
    }
    actions[args.action](kb, args)


if __name__ == "__main__":
    main()
