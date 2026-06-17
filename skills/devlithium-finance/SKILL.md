---
name: devlithium-finance
description: Use this skill for all pool fund management, expense tracking, and cost splitting in the Devlithium home. Triggers on "check pool fund", "how much money do we have", "log an expense", "split the cost", "add money to fund", "who owes what", "monthly expenses", or any finance-related request. Also triggers automatically when pool balance drops below ₹12,000. The minimum pool balance is ₹10,000 (~$100) — the model enforces this as a hard floor.
---

# devlithium-finance

Manages the shared pool fund for 3 residents. Tracks expenses, splits costs, monitors balance, and alerts when top-up is needed.

**Model rule**: Haiku task. Load only `house_kb.finance`.

## Data
- Read/Write: `house_kb.json` → `finance` section only

---

## Check Fund Balance
```bash
python skills/devlithium-finance/scripts/fund_check.py
```

Output:
```
💰 POOL FUND STATUS — [date]
Current balance: ₹[amount]
Status: 🟢 OK / 🟡 WARNING (<₹12,000) / 🔴 CRITICAL (<₹10,000)
Projected 7-day spend: ₹[amount]
Projected balance in 7 days: ₹[amount]
Per-person share if top-up needed: ₹[amount]
```

## Log an Expense
When any purchase is made from pool fund:
```bash
python skills/devlithium-finance/scripts/log_expense.py \
  --category "grocery" --item "vegetables" --amount 350 --paid_by "u1" --split "equal"
```
Categories: `grocery`, `cleaning`, `repair`, `utility`, `maintenance`, `other`

## Top-Up Request
When balance < ₹12,000 (warning) or < ₹10,000 (critical):
1. Calculate how much is needed to restore to ₹15,000 (safe buffer above minimum)
2. Divide equally (or by `fund_share_pct`)
3. Send notification to all residents with exact amount per person

Example alert:
```
⚠️ Pool Fund Alert — Devlithium House
Current balance: ₹9,400 (below minimum ₹10,000)
Please add ₹[amount] each to restore to ₹15,000.
Payment options: [UPI / bank transfer — to be configured]
```

## Monthly Summary
Run on 1st of each month OR when user asks "monthly expenses":
```bash
python skills/devlithium-finance/scripts/monthly_summary.py
```

Output:
```
📊 MONTHLY EXPENSE SUMMARY — [Month Year]
Total spent: ₹[amount]
  Grocery: ₹[amount]
  Cleaning: ₹[amount]
  Utilities: ₹[amount]
  Repairs: ₹[amount]
  Other: ₹[amount]
Per person (equal split): ₹[amount]
Savings from terrace farm: ₹[amount]
Net cost per person: ₹[amount]
```

## Reimbursement Tracking
If one resident pays more than their share:
1. Calculate deficit per resident
2. Log as "owed" in expense_log
3. Include in next weekly report

## Rules
- Never let balance go below ₹10,000 without alerting all residents
- Every expense > ₹0 must be logged — no untracked spending
- Bulk purchases > ₹500 require resident approval before logging
- Monthly fixed costs are auto-deducted on 1st of each month
