---
name: devlithium-notify
description: Use this skill to send notifications to house residents from the Devlithium Home Manager. Triggers when any module needs to alert residents — low inventory, fund alerts, repair updates, cleaning reminders, or social coordination. Also triggers on "notify residents", "send alert", "message the house", "tell everyone", "send the weekly digest". Uses email by default (free), with WhatsApp template ready for Phase 2 activation.
---

# devlithium-notify

The notification engine for Devlithium. Sends structured, minimal alerts to residents via email (Phase 1) and WhatsApp (Phase 2).

**Core rule**: Maximum 1 digest notification per day. Only send immediate alerts for CRITICAL events (fund below minimum, urgent repair, security issue).

## Notification Types

| Type | Priority | When Sent | Recipients |
|------|----------|-----------|------------|
| `daily_digest` | Low | Once per day (morning) | All residents |
| `fund_warning` | Medium | Balance < ₹12,000 | All residents |
| `fund_critical` | HIGH | Balance < ₹10,000 | All residents |
| `inventory_low` | Low | Bundled in daily digest | All residents |
| `repair_update` | Medium | When issue status changes | Relevant resident + admin |
| `cleaning_reminder` | Low | Day before cleaning | All residents |
| `topup_request` | HIGH | Fund needs replenishment | All residents + per-person amount |
| `social_suggestion` | Low | When calendar slots align | Relevant residents |
| `weekly_report` | Low | Every Monday | All residents |

---

## Phase 1: Email Notifications

Send via Python `smtplib` using Gmail SMTP (free, no API cost).

### Setup (one-time)
```bash
python skills/devlithium-notify/scripts/setup_email.py
```
Enter Gmail credentials (stored in `data/notify_config.json`, never in house_kb.json).

### Send a notification
```bash
python skills/devlithium-notify/scripts/send_email.py \
  --type "daily_digest" \
  --subject "🏠 Devlithium Daily — [date]" \
  --body "..." \
  --recipients "all"
```
`--recipients` accepts: `all`, `u1`, `u2`, `u3`, or comma-separated IDs.

---

## Message Templates

### Daily Digest
```
Subject: 🏠 Devlithium Daily — [Day, Date]

Hi [name],

Here's your house update for today:

🛒 Inventory: [OK / Low: milk, eggs]
💰 Pool Fund: ₹[balance] [status emoji]
🔧 Repairs: [None open / N issues]
🧹 Cleaning: [Next on Day, Date]

[If any action needed:]
Action needed: [specific ask — e.g., "Please reorder milk via Blinkit"]

— Devlithium 🏠
```

### Fund Critical Alert
```
Subject: 🔴 URGENT: Pool Fund Below Minimum — Action Required

Hi [name],

The house pool fund has fallen below ₹10,000 (current: ₹[amount]).

Please add ₹[per_person_amount] to the shared account by [deadline].
Your share: ₹[amount] (equal split among [N] residents)

[Payment details to be added in setup]

— Devlithium 🏠
```

### Weekly Report
```
Subject: 📊 Devlithium Weekly — [Date Range]

Hi team,

Week in review:
🛒 Grocery spend: ₹[amount] (₹[per_person] each)
💰 Pool Fund: ₹[balance]
🔧 Repairs resolved: [N]
🌱 Terrace savings: ₹[amount]

Net cost per person this week: ₹[amount]

[Top suggestion for next week]

— Devlithium 🏠
```

---

## Phase 2: WhatsApp (Twilio — not yet active)
When Twilio is set up:
1. Run `python skills/devlithium-notify/scripts/setup_whatsapp.py`
2. Enter Twilio credentials
3. Set `notify_config.json` → `"whatsapp_enabled": true`
4. All messages will then send to WhatsApp first, email as fallback

---

## Rules
- Never send personal data (phone, address) in notification body
- Never send more than 3 notifications per day to any resident (avoid notification fatigue)
- Bundle low-priority alerts into the daily digest
- Always include one clear call-to-action if action is needed
- Keep messages under 150 words
