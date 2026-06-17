# Handoff — Devlithium Home Manager
**Session:** S3 → S4 | 2026-06-17 | Branch: main @ 0a6db3f

## Active Work
Full web app — all 4 pages functional, mobile-ready, pushed to GitHub (private) ✅

## Done This Session
- GitHub repo created: https://github.com/rahuldev3160/devlithium-model (private)
  — Sensitive files gitignored: house_kb.json, auth_config.json, profiles/, logs/
  — Example templates added: web/auth_config.example.json, data/notify_config.example.json
- House page (`web/static/house.html`): 3-tab layout — Repairs CRUD, Inventory inline edit, Nudges (anonymous flags + Claude Haiku AI synthesis)
- My Room page (`web/static/my_room.html`): presence toggle (home/away/dnd), house inventory read-only view, quick actions
- Recurring bill templates (`web/app.py` + `web/static/residents.html`): GET/POST /api/finance/templates, POST /api/finance/templates/{id}/log with next_due_date by frequency
- Inventory starter quantities fixed via Python (all were 0 → above threshold, Supplies now shows ok)
- Backend endpoints added: /api/house/repairs (CRUD), /api/house/inventory (GET+PATCH), /api/house/flags (submit/list/synthesize)
- Mobile layer: `web/static/mobile.css` + `web/static/mobile-nav.js` — bottom nav, bottom sheets, 44px touch targets, 16px input font-size (iOS zoom fix), safe-area insets, all 5 pages wired

## Next Actions (start here)
1. **Fix login.html** — still shows old names (Dev/Sunil, missing Loki). Update `web/static/login.html` resident list to match auth_config.json: Rahul(u1), Sarita(u2), Hanu(u3), Loki(u4)
2. **Fix dashboard sidebar** — House and My Room still show `.dim` + "Soon" badge. Update `web/static/dashboard.html` lines 721-730 to link to `/house` and `/my-room` (remove `.dim`)
3. **Gmail App Password** — add to `data/notify_config.json` (get from myaccount.google.com/apppasswords). Required for email notifications to work.
4. **Fill contact details** — Hanu, Sarita, Loki still have FILL_IN for email/phone. Do via http://localhost:4200/residents (admin login)
5. **Test mobile on real device** — connect phone to same WiFi, open `http://<mac-ip>:4200`. Check bottom nav, presence toggle, repair modal bottom sheet.

## Files Modified This Session
- `web/app.py` — 6 new house endpoints + 3 template endpoints + _save_kb helper + timedelta import
- `web/static/house.html` — full build (was stub)
- `web/static/my_room.html` — full build (was stub)
- `web/static/residents.html` — recurring bills section added by Fork B
- `web/static/dashboard.html` — mobile.css link added
- `web/static/login.html` — mobile.css link added (nav injector skips it — no .main)
- `web/static/mobile.css` — new: full mobile stylesheet
- `web/static/mobile-nav.js` — new: bottom nav injector
- `data/house_kb.json` — inventory quantities updated, repair test entry added, flag test entry added
- `.gitignore` — expanded to cover house_kb.json, auth_config.json, profiles/, logs/
- `web/auth_config.example.json` — new
- `data/notify_config.example.json` — new

## Blockers
- Gmail App Password missing → email notifications blocked (user must provide)
- login.html has stale hardcoded resident list (Dev/Sunil, no Loki) — wrong names shown on login screen

## Key Decisions Made This Session
| Decision | What | Why | Rejected |
|---|---|---|---|
| DECIDE-10 | Private GitHub repo | house_kb.json has resident PINs + personal data | Public repo |
| DECIDE-11 | Gitignore: house_kb.json, auth_config.json, profiles/, logs/ | Real resident data — never in VCS | Scrubbing data in-place |
| DECIDE-12 | .example files for sensitive configs | Document structure without exposing values | README table |
| DECIDE-13 | Repairs stored in `services.repair.issues[]` (not `open_issues`) | Single array with status field — queryable | Separate open/closed arrays |
| DECIDE-14 | Anonymous flags — reporter_id never stored | Reduces conflict, preserves anonymity guarantee | Store with hash for auditing |
| DECIDE-15 | Synthesis clears pending flags | Clean slate after AI generates nudge | Keep flags forever |
| DECIDE-16 | Shared mobile.css + mobile-nav.js (injected) | One source of truth across 5 pages | Per-page mobile CSS blocks |
| DECIDE-17 | Bottom nav appears at 960px (matches sidebar hide) | No navigation gap between breakpoints | 768px (left gap 768-960) |
| DECIDE-18 | 16px font-size on all inputs | iOS zooms on < 16px — confirmed lesson from Nyaya Scribe pattern | Per-field override |
| DECIDE-19 | Modals → bottom sheets on mobile | Native feel, thumb reach — Nyaya Scribe mobile lesson | Centered modal at all sizes |

## Context Pointers
| Need | Read |
|---|---|
| House data / residents | `data/house_kb.json` |
| Model rules + routing | `CLAUDE.md` |
| Server start | `cd web && python3 -m uvicorn app:app --host 0.0.0.0 --port 4200` |
| All API endpoints | `web/app.py` |
| GitHub repo | https://github.com/rahuldev3160/devlithium-model |
