# Handoff — Devlithium Home Manager
**Session:** S2 → S3 | 2026-06-17 | No git (no branch)

## Active Work
Dashboard redesign — complete ✅  
Expense split engine — built and tested ✅  
Contact details UI — built ✅  
House / My Room pages — stubs only ⏳

## Done This Session

### Model restructure
- `CLAUDE.md` v2: stripped `devlithium-invest` + `devlithium-ventures` (belong to PFMS/Jarvis); Rule 8 income mandate removed; Expense Split Engine section added; Admin Users table added (Rahul/Hanu/Loki)
- `house_kb.json` v2.0: u2 → Sarita; u4 Loki added (delegate admin, `current_space` field); pool fund `monthly_contribution_per_resident: 2000`; `expense_split` section; `rental_potential` removed; all rooms have `is_billable` flag; `presence` field added to all residents

### Web UI — Residents page (`web/static/residents.html`)
- 4 resident cards (Rahul, Hanu, Sarita, Loki) with inline contact edit (email/phone)
- Bill split calculator: pre-loaded with ₹7,028 electricity bill; 4 room toggles; real-time split calc; logs to `finance.expense_log` via `POST /api/finance/bills`
- Expense history table
- Nav: updated to 4-section structure (Home / Expenses / House / My Room)
- Bug fix: "undefined" sub-text; "FILL_IN" shows as *Not set*

### Web UI — Dashboard (`web/static/dashboard.html`) — complete rewrite
- Removed: "Your Space" hero, personal finance panel, savings/portfolio, personal trips, exam nudges (UPSC/RBI/IES), Rishikesh hotel picker, Heads Up nudge list, private/shared zone split, notifications sidebar
- Added: health strip (3 pills: Money / House / Supplies with ok|warn|critical dots), urgent card (single, hidden when all ok), who's home strip (4 avatar circles with presence dots, tap own to cycle home→away→dnd), activity feed (live from expense_log), floating `+ Log` button (Expense / Repair / Note), sign-out moved to avatar dropdown
- Nav: 4 items only (Home / Expenses / House-soon / My Room-soon / Chat)

### Backend (`web/app.py`) — new endpoints
- `GET /api/dashboard` — combined health + presence + activity (single call)
- `PATCH /api/residents/{uid}/presence` — live presence updates; persists to house_kb.json
- `GET /api/residents` — updated to return room + email + phone from house_kb.json
- `PATCH /api/residents/{uid}` — save contact details (admin only)
- `POST /api/finance/bills` — log a bill, compute split, write to expense_log
- `GET /api/finance/bills` — list all logged bills
- Routes: `/residents`, `/house`, `/my-room`

### Stub pages
- `web/static/house.html` — placeholder (repairs, inventory, behavioral flags coming)
- `web/static/my_room.html` — placeholder (photos, AI suggestions, DND coming)

### auth_config.json
- u1 renamed Dev → Rahul; u2 Sunil → Sarita; u4 Loki added (pin: 0000, color: #A8844E)

### Live test confirmed
- `GET /api/dashboard` → returns real health + presence + activity (₹7,028 bill in feed)
- `PATCH /api/residents/u1/presence` → persists to house_kb.json
- All 4 page routes return 200

## Next Actions (start here)
1. **Fill in contact details**: Open `http://localhost:4200/residents` → Edit each card → add email/phone for Hanu, Sarita, Loki
2. **Fix inventory data**: All items have `current_qty: 0` → supplies shows critical. Update quantities in `data/house_kb.json` → `inventory.grocery[*].current_qty`
3. **Build House page** (`web/static/house.html`): repairs log (CRUD), inventory alerts, anonymous behavioral flag system (text + photo → AI synthesis into house nudge)
4. **Build My Room page** (`web/static/my_room.html`): photo upload, DND toggle (already wired to API), personal inventory
5. **Recurring bill templates**: electricity/internet auto-appear monthly in Expenses — implement in `POST /api/finance/bills` as a `recurring: true` flag + scheduler

## Files Modified
- `CLAUDE.md` (model identity, rules, agent routing, expense split engine)
- `data/house_kb.json` (residents, rooms, finance, presence fields)
- `web/auth_config.json` (Rahul, Sarita, Loki — 4 users)
- `web/app.py` (6 new endpoints + 3 new page routes)
- `web/static/dashboard.html` (complete rewrite)
- `web/static/residents.html` (contact editor + bill split + bug fixes + nav update)
- `web/static/house.html` (new — stub)
- `web/static/my_room.html` (new — stub)

## Blockers
- Gmail App Password still missing → email notifications to residents blocked (`data/notify_config.json`)
- Inventory quantities all 0 → house health shows critical for supplies (accurate but noisy until stocked)
- House / My Room pages are stubs — feature complete pages not yet built

## Key Decisions Made This Session
| Decision | What | Why | Rejected |
|---|---|---|---|
| DECIDE-01 | Devlithium scope = house manager only | Other projects (PFMS, Jarvis, Furmigdium) already own finance/ventures/investment | Was previously trying to do all of it |
| DECIDE-02 | Nav = Home / Expenses / House / My Room (4 sections) | Research across 18 apps: best have ≤4 top-level tabs | 7-item sidebar was overwhelming |
| DECIDE-03 | Dashboard = health strip + urgent card + who's home + activity feed only | House-first; no personal data on shared screen | Old "Your Space / The House" zone split |
| DECIDE-04 | Expense split threshold: <₹1k pool, ≥₹1k direct split | Keeps small costs frictionless, big bills need explicit awareness | Fixed ratio split |
| DECIDE-05 | Presence field on residents (home/away/dnd) | Real-time house awareness; no extra DB needed | Separate attendance log |
| DECIDE-06 | Activity feed from expense_log (no separate log) | Single source of truth; expense_log already has all actor + amount data | Separate activity_log table |
| DECIDE-07 | Admin set = Rahul + Hanu + Loki (delegate) | Loki manages when Rahul/Hanu unavailable | Admin = only owner |
| DECIDE-08 | Pool fund ₹2,000/month per resident | Covers ~50% of avg electricity + cleaning costs | Was undefined |
| DECIDE-09 | Anonymous behavioral flag system (planned, not built) | Both text + photo input; AI synthesizes into house nudge; anonymity reduces conflict | Named attribution |

## Context Pointers
| Need | Read |
|---|---|
| House data / residents | `data/house_kb.json` |
| Model rules + routing | `CLAUDE.md` |
| Server start command | `cd web && python3 -m uvicorn app:app --host 0.0.0.0 --port 4200` |
| Expense split API | `POST /api/finance/bills` in `web/app.py` |
| Research: 18 house apps surveyed | In S2 conversation (not persisted to file) |
