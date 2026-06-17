---
name: devlithium-repair
description: Use this skill for any repair, maintenance, or home fix request. Triggers on "something is broken", "fix the [item]", "AC not working", "plumber needed", "repair issue", "maintenance request", or any home defect report. Logs the issue, finds the cheapest verified provider, requests resident approval (required gate), then tracks the repair to completion.
---

# devlithium-repair

Manages the full lifecycle of home repair and maintenance issues — from intake to resolution. Finds cheapest provider, enforces approval gates, and syncs costs to `devlithium-finance`.

**Model rule**: Haiku task. Load only `house_kb.services.repair`. Escalate to Sonnet only for provider comparison reasoning.

## Data
- Read/Write: `house_kb.json` → `services.repair.open_issues` section only

---

## 1. Issue Intake (Log a New Problem)

When a resident reports any defect, breakage, or maintenance need:

```bash
python skills/devlithium-repair/scripts/repair_manager.py \
  --action log \
  --description "AC not cooling in master bedroom" \
  --room r1 \
  --priority high
```

Each issue is stored with these fields:
```json
{
  "id": "REP-001",
  "description": "AC not cooling in master bedroom",
  "room_id": "r1",
  "reported_by": "u1",
  "reported_date": "YYYY-MM-DD",
  "priority": "high",
  "status": "open",
  "provider_quotes": [],
  "approved_by": null,
  "scheduled_date": null,
  "resolved_date": null,
  "cost_inr": null
}
```

Priority levels: `low` | `medium` | `high` | `critical`
- `critical`: No water, no power, gas leak, flooding → immediate action, no delay
- `high`: AC, fridge, geyser, main door — resolve within 24 hours
- `medium`: Leaky tap, fan wobble, minor electrical — resolve within 3 days
- `low`: Cosmetic, paint, non-urgent fixes — resolve within 1 week

---

## 2. Provider Lookup

**Always check in this order:**
1. **Urban Company** (preferred — verified, insured, rated) → check via `services.delivery_apps.repair`
2. **Sulekha** (backup for specialised work)
3. **Local contacts** from `house_kb` (cheapest, use for small jobs)

**Quote rule**: If estimated cost > ₹500, **always get at least 2 quotes** before recommending.

```bash
# After getting quotes, add them to the issue:
python skills/devlithium-repair/scripts/repair_manager.py \
  --action quote \
  --id REP-001 \
  --provider "Urban Company" \
  --cost 850
```

Output format when comparing quotes:
```
🔧 PROVIDER QUOTES — REP-001: AC not cooling
  1. Urban Company    ₹850  ★ Recommended (verified, insured)
  2. Local HVAC       ₹600  ⚠️ Unverified — use only if resident approves
Cheapest verified:  Urban Company @ ₹850
Cheapest overall:   Local HVAC @ ₹600
```

---

## 3. Approval Gate (MANDATORY)

**ALWAYS require Dev (u1) approval before booking if:**
- Cost > ₹500 (pool fund rule from CLAUDE.md)
- Any physical change to the house (drilling, installation, replacement)
- First-time provider (not previously used)

**Never skip this gate.** Send approval request via `devlithium-notify`:
```
🔧 Repair Approval Needed — [issue description]
Room: [room name]
Priority: [priority]
Recommended: [provider] @ ₹[cost]
Cheaper option: [provider] @ ₹[cost] (unverified)

Reply APPROVE or REJECT.
```

Once approved:
```bash
python skills/devlithium-repair/scripts/repair_manager.py \
  --action approve \
  --id REP-001 \
  --approved_by u1 \
  --provider "Urban Company" \
  --cost 850
```

---

## 4. Scheduling

Once approved, log the scheduled date and notify the relevant room occupant:

```bash
python skills/devlithium-repair/scripts/repair_manager.py \
  --action schedule \
  --id REP-001 \
  --scheduled_date 2026-05-16
```

Notification to room occupant:
```
🔧 Repair Scheduled — [description]
Provider: [name]
Date: [date]
Please ensure access to [room] from [time window].
```

Status transitions: `open` → `approved` → `scheduled` → `in_progress` → `resolved`

---

## 5. Completion & Cost Logging

When repair is confirmed done:

```bash
python skills/devlithium-repair/scripts/repair_manager.py \
  --action resolve \
  --id REP-001 \
  --cost 850
```

This script automatically:
1. Marks issue `status: resolved`, logs `resolved_date`
2. Calls `devlithium-finance` to log the cost:
   ```bash
   python skills/devlithium-finance/scripts/log_expense.py \
     --category repair --item "[description]" --amount [cost] --paid_by u1 --split equal
   ```
3. Updates `house_kb._meta.last_updated`
4. Prints confirmation summary

---

## 6. Status & List

```bash
# View all open issues
python skills/devlithium-repair/scripts/repair_manager.py --action list

# View a specific issue
python skills/devlithium-repair/scripts/repair_manager.py --action status --id REP-001
```

List output format:
```
🔧 OPEN REPAIR ISSUES — 2026-05-15
=====================================
REP-001  🔴 HIGH     AC not cooling (r1)     Open 2 days
REP-002  🟡 MEDIUM   Leaky tap (r4)          Open 1 day
=====================================
Total open: 2 | Scheduled: 0 | Resolved this month: 1
```

---

## 7. Escalation (Daily Check Hook)

Called by `devlithium-daily` in Step 4 (Repair Check):
```bash
python skills/devlithium-repair/scripts/repair_manager.py --action list
```

Escalation rules (checked automatically):
- Issue `status: open` AND `age_days >= 3` → re-notify Dev, flag in daily digest
- Issue `priority: critical` AND `age_days >= 1` → immediate alert, page Dev
- Issue `status: scheduled` AND `scheduled_date == today` → send reminder to room occupant

---

## Rules
- Never book a provider without explicit approval (cost > ₹500 or physical change)
- Always log the cheapest verified option in quotes, even if not chosen
- All repair costs sync to `devlithium-finance` — no untracked spending
- Issue IDs increment: REP-001, REP-002, ... (check existing issues for next ID)
- `critical` issues bypass normal queue — immediate escalation to Dev regardless of time
