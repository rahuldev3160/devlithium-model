---
name: devlithium-daily
description: Use this skill for the Devlithium daily morning check, weekly house report, or any time the home manager needs to run its full coordination loop. Triggers on "run daily check", "morning check", "house status", "weekly report", "what does the house need today", or any autonomous coordination request. This is the master coordinator — it reads the house state, delegates to module skills, and writes the self-learning log.
---

# devlithium-daily

The master daily coordinator. Runs every morning (or on-demand) to check the house state, act on issues, and write the nightly learning log.

**Model Rule**: Use Haiku for all data reads and routine checks. Escalate to Sonnet only if reasoning is required.

## Data Files
- Read: `data/house_kb.json`
- Write log: `logs/daily_log.jsonl`

---

## Daily Check Sequence

Run all checks in this order. Stop early only if a critical issue is found that needs immediate human input.

### 1. Read Yesterday's Log
```bash
python skills/devlithium-daily/scripts/read_log.py --last 1
```
Check: any open items from yesterday? If yes, add to today's action list first.

### 2. Inventory Check
Load `house_kb.inventory`. For each item where `current_qty <= reorder_threshold`:
- Flag for reorder
- If `auto_order: true` → trigger `devlithium-inventory` reorder flow
- If `auto_order: false` → add to notification digest

### 3. Finance Check
Load `house_kb.finance.pool_fund`:
- If `current_balance < alert_threshold (12000)` → send warning notification
- If `current_balance < minimum_balance (10000)` → send CRITICAL alert, request top-up
- Calculate: next 7 days expected spend based on `monthly_fixed_costs / 4`
- Flag if projected balance will fall below ₹10,000 in 7 days

### 4. Repair Check
Load `house_kb.services.repair.open_issues`:
- For each issue with `status: open` and `age_days > 3` → escalate, re-notify
- For each issue with `status: scheduled` → confirm appointment

### 5. Cleaning Check
Load `house_kb.services.cleaning`:
- If `next_scheduled` is today or overdue → send reminder
- If `last_cleaned` is > 7 days ago and no schedule → flag

### 6. Sustainability Pulse (weekly only)
Run this block only on Mondays OR if `session_type == "weekly"`:
- Calculate: actual grocery spend vs terrace farm savings this week
- Check terrace farm `crops` — any harvest due?
- Update `estimated_monthly_savings_inr` if data available

### 7. Compile Notification Digest
Aggregate all flags from steps 2–6 into one notification. Send via `devlithium-notify`.
**Rule**: Never send more than 1 notification per day unless it's a CRITICAL alert.

### 8. Write Nightly Log
```bash
python skills/devlithium-daily/scripts/write_log.py \
  --date TODAY \
  --session_type "daily" \
  --actions "list of actions taken" \
  --what_worked "..." \
  --what_failed "..." \
  --cost 0 \
  --income 0 \
  --open_items "..."
```

---

## Weekly Report Mode
Triggered when user says "weekly report" or it's Monday.
In addition to the daily sequence, generate a summary:
```
📊 DEVLITHIUM WEEKLY REPORT — [date range]

🛒 Inventory: [N items reordered] | ₹[amount spent]
💰 Pool Fund: ₹[balance] | [+/-% vs last week]
🔧 Repairs: [N open] | [N resolved]
🌱 Sustainability: ₹[savings from terrace] | ₹[rental income]
📈 Net Cost This Week: ₹[amount] | Per Person: ₹[amount]

⚠️ Alerts: [any pending issues]
✅ All clear: [what's working well]
```
Save to `logs/weekly_report_[date].md` and send to all residents.

---

## Output Format (daily)
```
🏠 DEVLITHIUM DAILY CHECK — [date]

✅ Inventory: [OK / N items low]
✅ Finance: ₹[balance] ([status])
✅ Repairs: [N open issues]
✅ Cleaning: [next on date]

📲 Notification sent to: [residents]
📝 Log written.
```
