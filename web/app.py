"""
Devlithium Web Server
Local-only FastAPI app. Serves the frontend and provides API endpoints.
Run: uvicorn app:app --host 0.0.0.0 --port 4200
"""
import json
import os
import secrets
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

import anthropic
from fastapi import Body, Cookie, FastAPI, Form, HTTPException, Request, Response
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

BASE = Path(__file__).parent.parent
DATA = BASE / "data"
LOGS = BASE / "logs"
WEB  = Path(__file__).parent

app = FastAPI(title="Devlithium")

# ── In-memory sessions: {session_id: user_id} ──────────────────────────────
SESSIONS: dict[str, str] = {}

# ── Load auth config (PINs) ─────────────────────────────────────────────────
AUTH_FILE = WEB / "auth_config.json"

def load_auth() -> dict:
    if not AUTH_FILE.exists():
        default = {
            "u1": {"pin": "1234", "name": "Dev",   "color": "#3B5FA0"},
            "u2": {"pin": "0000", "name": "Sunil", "color": "#A8844E"},
            "u3": {"pin": "0000", "name": "Hanu",  "color": "#3A7A5A"},
        }
        AUTH_FILE.write_text(json.dumps(default, indent=2))
    return json.loads(AUTH_FILE.read_text())

def get_session_user(session_id: Optional[str]) -> Optional[str]:
    if not session_id:
        return None
    return SESSIONS.get(session_id)

def load_profile(uid: str) -> dict:
    path = DATA / "profiles" / f"{uid}.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}

def load_kb() -> dict:
    path = DATA / "house_kb.json"
    if path.exists():
        return json.loads(path.read_text())
    return {}

def load_events_log() -> list:
    path = LOGS / "events_log.jsonl"
    if not path.exists():
        return []
    lines = path.read_text().strip().splitlines()
    events = []
    for line in lines:
        try:
            events.append(json.loads(line))
        except Exception:
            pass
    return events

# ── Static files ─────────────────────────────────────────────────────────────
app.mount("/static", StaticFiles(directory=WEB / "static"), name="static")

# ── Routes ───────────────────────────────────────────────────────────────────

@app.get("/")
def root(dlsession: Optional[str] = Cookie(default=None)):
    uid = get_session_user(dlsession)
    if uid:
        return RedirectResponse("/dashboard")
    return RedirectResponse("/login")

@app.get("/login")
def login_page():
    return FileResponse(WEB / "static" / "login.html")

@app.get("/dashboard")
def dashboard_page(dlsession: Optional[str] = Cookie(default=None)):
    if not get_session_user(dlsession):
        return RedirectResponse("/login")
    return FileResponse(WEB / "static" / "dashboard.html")

# ── API ───────────────────────────────────────────────────────────────────────

@app.post("/api/login")
def api_login(response: Response, user_id: str = Form(...), pin: str = Form(...)):
    auth = load_auth()
    if user_id not in auth:
        raise HTTPException(status_code=401, detail="Unknown resident")
    if auth[user_id]["pin"] != pin:
        raise HTTPException(status_code=401, detail="Wrong PIN")
    session_id = secrets.token_urlsafe(32)
    SESSIONS[session_id] = user_id
    response.set_cookie(
        key="dlsession", value=session_id,
        httponly=True, samesite="lax", max_age=60 * 60 * 24 * 7  # 7 days
    )
    return {"ok": True, "user_id": user_id, "name": auth[user_id]["name"]}

@app.post("/api/logout")
def api_logout(response: Response, dlsession: Optional[str] = Cookie(default=None)):
    if dlsession and dlsession in SESSIONS:
        del SESSIONS[dlsession]
    response.delete_cookie("dlsession")
    return {"ok": True}

@app.get("/api/me")
def api_me(dlsession: Optional[str] = Cookie(default=None)):
    uid = get_session_user(dlsession)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    auth = load_auth()
    profile = load_profile(uid)
    return {
        "user_id": uid,
        "name": auth[uid]["name"],
        "color": auth[uid]["color"],
        "role": profile.get("_meta", {}).get("role", "resident"),
    }

@app.get("/api/dashboard/private")
def api_private(dlsession: Optional[str] = Cookie(default=None)):
    uid = get_session_user(dlsession)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    profile = load_profile(uid)
    fin = profile.get("financial", {})
    goals = profile.get("goals", {})
    trips = profile.get("locations", {}).get("travel_preferences", {}).get("upcoming_trips", [])
    career = goals.get("career", [])
    return {
        "liquidity_inr": fin.get("liquidity", {}).get("total_liquid_inr", 0),
        "portfolio_inr": fin.get("assets", {}).get("investments", {}).get("total_portfolio_inr", 0),
        "monthly_income_inr": fin.get("monthly_income", {}).get("total_inr", 0),
        "upcoming_trips": trips,
        "career_goals": career,
        "risk_appetite": fin.get("risk_appetite"),
    }

@app.get("/api/dashboard/shared")
def api_shared(dlsession: Optional[str] = Cookie(default=None)):
    if not get_session_user(dlsession):
        raise HTTPException(status_code=401, detail="Not logged in")
    kb = load_kb()
    fin = kb.get("finance", {})
    repairs = kb.get("repairs", {})
    inventory = kb.get("inventory", {})
    events = load_events_log()

    upcoming = sorted(
        [e for e in events if e.get("status") == "planned"],
        key=lambda x: x.get("dates", x.get("date", "")),
    )

    low_items = []
    for section in inventory.values() if isinstance(inventory, dict) else []:
        if isinstance(section, list):
            for item in section:
                if isinstance(item, dict) and item.get("status") in ("low", "out"):
                    low_items.append(item.get("name", "Unknown"))

    return {
        "pool_fund_inr": fin.get("pool_fund", {}).get("balance_inr", 0),
        "pool_fund_target_inr": fin.get("pool_fund", {}).get("monthly_target_inr", 24000),
        "open_repairs": len([r for r in (repairs if isinstance(repairs, list) else []) if r.get("status") == "open"]),
        "low_inventory": low_items,
        "upcoming_events": upcoming[:4],
    }

@app.get("/api/notifications")
def api_notifications(dlsession: Optional[str] = Cookie(default=None)):
    uid = get_session_user(dlsession)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    # Hardcoded seed notifications — will be driven by skills in future
    shared = [
        {"id": "n1", "type": "finance",   "dot": "terra", "text": "Pool fund ₹5,600 below monthly target. Top-up reminder sent to all residents.", "time": "9:02", "shared": True},
        {"id": "n2", "type": "events",    "dot": "blue",  "text": "Rishikesh solo trip confirmed May 25–27. Housemates notified of Dev's absence.", "time": "8:50", "shared": True},
        {"id": "n3", "type": "inventory", "dot": "green", "text": "Coffee and bread running low — Blinkit reorder suggested before May 18.", "time": "7:30", "shared": True},
    ]
    private_map = {
        "u1": [
            {"id": "p1", "type": "finance", "dot": "gold", "text": "Cash flow runway is 5.3 months. ₹19k/month burn rate.", "time": "9:05", "shared": False},
            {"id": "p2", "type": "exam",    "dot": "terra","text": "UPSC Prelims in 9 days. Bike service on May 19 — confirmed.", "time": "8:00", "shared": False},
        ],
        "u2": [
            {"id": "p1", "type": "finance", "dot": "gold", "text": "Pool fund share: ₹6,133 / month due.", "time": "9:05", "shared": False},
        ],
        "u3": [
            {"id": "p1", "type": "house",   "dot": "blue", "text": "You own this house. Hanu, your office (r7) inventory is up to date.", "time": "9:05", "shared": False},
        ],
    }
    return {
        "shared": shared,
        "private": private_map.get(uid, []),
    }

@app.post("/api/chat")
async def api_chat(
    dlsession: Optional[str] = Cookie(default=None),
    body: dict = Body(...),
):
    uid = get_session_user(dlsession)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")

    message = body.get("message", "").strip()
    history = body.get("history", [])   # [{role, content}, ...]
    if not message:
        raise HTTPException(status_code=400, detail="Empty message")

    profile = load_profile(uid)
    kb = load_kb()
    auth = load_auth()
    name = auth[uid]["name"]

    system_prompt = f"""You are Devlithium, an autonomous home intelligence AI for a 3-resident household in Jaipur, India (T-1, 1/54, 3rd Floor, Jaipur 302021).

You are talking to {name} (user ID: {uid}).

Resident profile summary:
{json.dumps(profile, indent=2, ensure_ascii=False)[:3000]}

House knowledge base summary:
{json.dumps(kb, indent=2, ensure_ascii=False)[:2000]}

Today's date: {datetime.now().strftime('%A, %d %B %Y')}.

Guidelines:
- Be concise, warm, and practical. You know this household well.
- For Dev (u1): he has UPSC Prelims on May 24, RBI Grade B exam June 16, IES June 19-20. Treat exam prep as his top priority during study hours (8am-11pm).
- Speak like a trusted home assistant — not a corporate chatbot.
- Use Indian context naturally (₹, local references, etc).
- Keep replies under 150 words unless the user asks for detail."""

    messages = []
    for h in history[-6:]:  # last 6 turns for context
        if h.get("role") in ("user", "assistant") and h.get("content"):
            messages.append({"role": h["role"], "content": h["content"]})
    messages.append({"role": "user", "content": message})

    client = anthropic.Anthropic()

    def stream_response():
        with client.messages.stream(
            model="claude-haiku-4-5-20251001",
            max_tokens=400,
            system=system_prompt,
            messages=messages,
        ) as stream:
            for text in stream.text_stream:
                yield text

    return StreamingResponse(stream_response(), media_type="text/plain")


@app.get("/api/residents")
def api_residents(dlsession: Optional[str] = Cookie(default=None)):
    if not get_session_user(dlsession):
        raise HTTPException(status_code=401, detail="Not logged in")
    auth = load_auth()
    kb = load_kb()
    kb_residents = {r["id"]: r for r in kb.get("residents", [])}
    roles = {"u1": "Admin", "u2": "Resident", "u3": "Owner", "u4": "Admin"}
    rooms_map = {r["id"]: r["name"] for r in kb.get("rooms", [])}
    result = []
    for uid, info in auth.items():
        kb_r = kb_residents.get(uid, {})
        room_id = kb_r.get("room_id") or kb_r.get("current_space")
        result.append({
            "id": uid,
            "name": info["name"],
            "color": info["color"],
            "role": roles.get(uid, "Resident"),
            "room": rooms_map.get(room_id, "—") if room_id else "—",
            "email": kb_r.get("email", ""),
            "phone": kb_r.get("phone", ""),
        })
    return result


@app.get("/residents")
def residents_page(dlsession: Optional[str] = Cookie(default=None)):
    if not get_session_user(dlsession):
        return RedirectResponse("/login")
    return FileResponse(WEB / "static" / "residents.html")


@app.patch("/api/residents/{res_uid}")
async def api_update_resident(
    res_uid: str,
    dlsession: Optional[str] = Cookie(default=None),
    body: dict = Body(...),
):
    uid = get_session_user(dlsession)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    kb = load_kb()
    admins = kb.get("_meta", {}).get("admins", ["u1"])
    if uid not in admins:
        raise HTTPException(status_code=403, detail="Admin access required")

    allowed = {"email", "phone", "whatsapp"}
    for r in kb.get("residents", []):
        if r["id"] == res_uid:
            for k, v in body.items():
                if k in allowed:
                    r[k] = v
            break
    else:
        raise HTTPException(status_code=404, detail="Resident not found")

    kb["_meta"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    (DATA / "house_kb.json").write_text(json.dumps(kb, indent=2, ensure_ascii=False))
    return {"ok": True}


@app.post("/api/finance/bills")
async def api_log_bill(
    dlsession: Optional[str] = Cookie(default=None),
    body: dict = Body(...),
):
    uid = get_session_user(dlsession)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    kb = load_kb()
    admins = kb.get("_meta", {}).get("admins", ["u1"])
    if uid not in admins:
        raise HTTPException(status_code=403, detail="Admin access required")

    amount = float(body.get("amount_inr", 0))
    description = body.get("description", "Expense")
    category = body.get("category", "utility")
    included_rooms = body.get("included_rooms", [])

    rooms_map = {r["id"]: r for r in kb.get("rooms", [])}
    residents_map = {r["id"]: r for r in kb.get("residents", [])}

    splits = []
    for room_id in included_rooms:
        room = rooms_map.get(room_id)
        if not room:
            continue
        occ_id = room.get("occupant_id")
        occ_name = residents_map[occ_id]["name"] if occ_id and occ_id in residents_map else "Vacant"
        splits.append({
            "room_id": room_id,
            "room_name": room["name"],
            "occupant_id": occ_id,
            "occupant_name": occ_name,
        })

    if not splits:
        raise HTTPException(status_code=400, detail="No valid rooms selected")

    share = round(amount / len(splits), 2)
    for s in splits:
        s["share_inr"] = share

    method = "direct_split" if amount >= 1000 else "pool_deduction"
    entry = {
        "id": f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "date": datetime.now().strftime("%Y-%m-%d"),
        "category": category,
        "description": description,
        "amount_inr": amount,
        "method": method,
        "num_spaces": len(splits),
        "share_per_space_inr": share,
        "splits": splits,
        "logged_by": uid,
    }

    kb["finance"]["expense_log"].append(entry)
    kb["_meta"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    (DATA / "house_kb.json").write_text(json.dumps(kb, indent=2, ensure_ascii=False))
    return {"ok": True, "entry": entry}


@app.get("/api/finance/bills")
def api_get_bills(dlsession: Optional[str] = Cookie(default=None)):
    uid = get_session_user(dlsession)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    kb = load_kb()
    return kb.get("finance", {}).get("expense_log", [])


# ── New dashboard endpoints (v2) ──────────────────────────────────────────────

@app.get("/api/dashboard")
def api_dashboard(dlsession: Optional[str] = Cookie(default=None)):
    uid = get_session_user(dlsession)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")

    kb = load_kb()

    # ── Health ──
    pool    = kb.get("finance", {}).get("pool_fund", {})
    balance = pool.get("current_balance", 0)
    alert   = pool.get("alert_threshold", 12000)
    minimum = pool.get("minimum_balance", 10000)

    if balance <= minimum:
        money_status = "critical"
    elif balance <= alert:
        money_status = "warn"
    else:
        money_status = "ok"

    money_note = f"₹{alert - balance:,.0f} below target" if balance < alert else "Pool fund healthy"

    all_issues   = kb.get("services", {}).get("repair", {}).get("issues", [])
    open_repairs = [i for i in all_issues if i.get("status") == "open"]
    num_repairs  = len(open_repairs)
    house_status = "critical" if num_repairs >= 3 else "warn" if num_repairs >= 1 else "ok"
    house_note   = f"{num_repairs} open" if num_repairs else "All clear"

    low_items = []
    for section in kb.get("inventory", {}).values():
        if isinstance(section, list):
            for item in section:
                if isinstance(item, dict) and item.get("current_qty", 1) <= item.get("reorder_threshold", 0):
                    low_items.append(item.get("item", "item").split(" (")[0])

    supplies_status = "critical" if len(low_items) >= 4 else "warn" if low_items else "ok"
    supplies_note   = " · ".join(low_items[:3]) if low_items else "All stocked"

    health = {
        "money":    {"status": money_status,    "label": f"₹{balance:,.0f}",                        "note": money_note},
        "house":    {"status": house_status,    "label": f"{num_repairs} repair{'s' if num_repairs != 1 else ''}", "note": house_note},
        "supplies": {"status": supplies_status, "label": f"{len(low_items)} low" if low_items else "All stocked", "note": supplies_note},
    }

    # ── Presence ──
    auth     = load_auth()
    presence = []
    for r in kb.get("residents", []):
        uid_r = r["id"]
        if uid_r in auth:
            presence.append({
                "id":       uid_r,
                "name":     auth[uid_r]["name"],
                "color":    auth[uid_r]["color"],
                "presence": r.get("presence", "home"),
            })

    # ── Activity feed — built from expense_log ──
    auth_map = auth
    activity = []
    for exp in reversed(kb.get("finance", {}).get("expense_log", [])[-20:]):
        logged_by = exp.get("logged_by", "u1")
        actor     = auth_map.get(logged_by, {})
        share     = exp.get("share_per_space_inr", 0)
        desc      = exp.get("description", "Expense")
        amt       = exp.get("amount_inr", 0)
        activity.append({
            "id":          exp.get("id", ""),
            "type":        "expense",
            "text":        f"{desc} ₹{amt:,.0f} · split {exp.get('num_spaces', 1)} ways (₹{share:,.0f}/space)",
            "actor_name":  actor.get("name"),
            "actor_color": actor.get("color"),
            "time_ago":    exp.get("date", ""),
            "icon":        "💡" if "electric" in desc.lower() else "💰",
        })

    if not activity:
        activity = [{"id": "seed1", "type": "note", "text": "House manager active · welcome to Devlithium",
                     "actor_name": None, "actor_color": None, "time_ago": "today", "icon": "🏠"}]

    return {"health": health, "presence": presence, "activity": activity[:8]}


@app.patch("/api/residents/{res_uid}/presence")
async def api_update_presence(
    res_uid: str,
    dlsession: Optional[str] = Cookie(default=None),
    body: dict = Body(...),
):
    uid = get_session_user(dlsession)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")

    kb     = load_kb()
    admins = kb.get("_meta", {}).get("admins", ["u1"])
    if uid != res_uid and uid not in admins:
        raise HTTPException(status_code=403, detail="Can only update your own presence")

    new_presence = body.get("presence", "home")
    if new_presence not in ("home", "away", "dnd"):
        raise HTTPException(status_code=400, detail="presence must be home|away|dnd")

    for r in kb.get("residents", []):
        if r["id"] == res_uid:
            r["presence"] = new_presence
            break
    else:
        raise HTTPException(status_code=404, detail="Resident not found")

    kb["_meta"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    (DATA / "house_kb.json").write_text(json.dumps(kb, indent=2, ensure_ascii=False))
    return {"ok": True, "presence": new_presence}


@app.get("/house")
def house_page(dlsession: Optional[str] = Cookie(default=None)):
    if not get_session_user(dlsession):
        return RedirectResponse("/login")
    return FileResponse(WEB / "static" / "house.html")


@app.get("/my-room")
def my_room_page(dlsession: Optional[str] = Cookie(default=None)):
    if not get_session_user(dlsession):
        return RedirectResponse("/login")
    return FileResponse(WEB / "static" / "my_room.html")


# ── House: Repairs ────────────────────────────────────────────────────────────

def _save_kb(kb: dict):
    kb["_meta"]["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    (DATA / "house_kb.json").write_text(json.dumps(kb, indent=2, ensure_ascii=False))


@app.get("/api/house/repairs")
def api_get_repairs(dlsession: Optional[str] = Cookie(default=None)):
    if not get_session_user(dlsession):
        raise HTTPException(status_code=401, detail="Not logged in")
    kb = load_kb()
    issues = kb.get("services", {}).get("repair", {}).get("issues", [])
    auth = load_auth()
    rooms_map = {r["id"]: r["name"] for r in kb.get("rooms", [])}
    residents_map = {r["id"]: r["name"] for r in kb.get("residents", [])}
    result = []
    for i in issues:
        result.append({
            **i,
            "room_name": rooms_map.get(i.get("room_id", ""), "—"),
            "reporter_name": auth.get(i.get("reported_by", ""), {}).get("name", "Resident"),
        })
    return result


@app.post("/api/house/repairs")
async def api_add_repair(
    dlsession: Optional[str] = Cookie(default=None),
    body: dict = Body(...),
):
    uid = get_session_user(dlsession)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    title = body.get("title", "").strip()
    if not title:
        raise HTTPException(status_code=400, detail="Title required")
    kb = load_kb()
    repair_svc = kb.setdefault("services", {}).setdefault("repair", {})
    issues = repair_svc.setdefault("issues", [])
    issue = {
        "id":            f"rep_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "title":         title,
        "description":   body.get("description", ""),
        "room_id":       body.get("room_id"),
        "urgency":       body.get("urgency", "medium"),
        "status":        "open",
        "reported_by":   uid,
        "reported_date": datetime.now().strftime("%Y-%m-%d"),
        "resolved_date": None,
        "provider":      None,
        "cost_inr":      None,
    }
    issues.append(issue)
    _save_kb(kb)
    return {"ok": True, "issue": issue}


@app.patch("/api/house/repairs/{repair_id}")
async def api_update_repair(
    repair_id: str,
    dlsession: Optional[str] = Cookie(default=None),
    body: dict = Body(...),
):
    uid = get_session_user(dlsession)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    kb = load_kb()
    admins = kb.get("_meta", {}).get("admins", ["u1"])
    issues = kb.get("services", {}).get("repair", {}).get("issues", [])
    for issue in issues:
        if issue["id"] == repair_id:
            if "status" in body:
                new_status = body["status"]
                if new_status not in ("open", "in_progress", "resolved"):
                    raise HTTPException(status_code=400, detail="Invalid status")
                if new_status == "resolved" and uid not in admins:
                    raise HTTPException(status_code=403, detail="Only admins can resolve repairs")
                issue["status"] = new_status
                if new_status == "resolved":
                    issue["resolved_date"] = datetime.now().strftime("%Y-%m-%d")
            for field in ("provider", "cost_inr"):
                if field in body:
                    issue[field] = body[field]
            _save_kb(kb)
            return {"ok": True}
    raise HTTPException(status_code=404, detail="Repair not found")


# ── House: Inventory ──────────────────────────────────────────────────────────

@app.get("/api/house/inventory")
def api_get_inventory(dlsession: Optional[str] = Cookie(default=None)):
    if not get_session_user(dlsession):
        raise HTTPException(status_code=401, detail="Not logged in")
    kb = load_kb()
    result = []
    for section_name, items in kb.get("inventory", {}).items():
        if not isinstance(items, list):
            continue
        for item in items:
            qty = item.get("current_qty", 0)
            threshold = item.get("reorder_threshold", 0)
            status = "out" if qty == 0 else "low" if qty <= threshold else "ok"
            result.append({
                "section":           section_name,
                "item":              item.get("item", ""),
                "unit":              item.get("unit", ""),
                "current_qty":       qty,
                "reorder_threshold": threshold,
                "status":            status,
                "supplier":          item.get("supplier", ""),
            })
    return result


@app.patch("/api/house/inventory")
async def api_update_inventory(
    dlsession: Optional[str] = Cookie(default=None),
    body: dict = Body(...),
):
    uid = get_session_user(dlsession)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    kb = load_kb()
    admins = kb.get("_meta", {}).get("admins", ["u1"])
    if uid not in admins:
        raise HTTPException(status_code=403, detail="Admin access required")
    item_name = body.get("item")
    new_qty = body.get("current_qty")
    if item_name is None or new_qty is None:
        raise HTTPException(status_code=400, detail="item and current_qty required")
    for section in kb.get("inventory", {}).values():
        if not isinstance(section, list):
            continue
        for item in section:
            if item.get("item") == item_name:
                item["current_qty"] = float(new_qty)
                _save_kb(kb)
                return {"ok": True}
    raise HTTPException(status_code=404, detail="Item not found")


# ── House: Behavioral Flags ───────────────────────────────────────────────────

@app.get("/api/house/flags")
def api_get_flags(dlsession: Optional[str] = Cookie(default=None)):
    if not get_session_user(dlsession):
        raise HTTPException(status_code=401, detail="Not logged in")
    kb = load_kb()
    return {"flags": kb.get("house_flags", []), "nudges": kb.get("house_nudges", [])}


@app.post("/api/house/flags")
async def api_submit_flag(
    dlsession: Optional[str] = Cookie(default=None),
    body: dict = Body(...),
):
    uid = get_session_user(dlsession)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    text = body.get("text", "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Flag text required")
    kb = load_kb()
    flag = {
        "id":   f"flag_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "text": text,
        "date": datetime.now().strftime("%Y-%m-%d"),
        # reporter intentionally not stored
    }
    kb.setdefault("house_flags", []).append(flag)
    _save_kb(kb)
    return {"ok": True}


@app.post("/api/house/flags/synthesize")
async def api_synthesize_flags(dlsession: Optional[str] = Cookie(default=None)):
    uid = get_session_user(dlsession)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    kb = load_kb()
    admins = kb.get("_meta", {}).get("admins", ["u1"])
    if uid not in admins:
        raise HTTPException(status_code=403, detail="Admin access required")
    flags = kb.get("house_flags", [])
    if not flags:
        raise HTTPException(status_code=400, detail="No flags to synthesize")
    flag_lines = "\n".join(f"- {f['text']} ({f['date']})" for f in flags)
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=200,
        messages=[{
            "role": "user",
            "content": (
                "You are Devlithium, a home manager AI for a shared house. "
                "These are anonymous concerns raised by residents:\n\n"
                f"{flag_lines}\n\n"
                "Write a single, warm, diplomatic house nudge that addresses these concerns. "
                "Under 60 words. No bullet points. No names. No accusatory tone."
            ),
        }],
    )
    nudge_text = response.content[0].text.strip()
    nudge = {
        "id":                f"nudge_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "text":              nudge_text,
        "date":              datetime.now().strftime("%Y-%m-%d"),
        "flags_synthesized": len(flags),
    }
    kb.setdefault("house_nudges", []).append(nudge)
    kb["house_flags"] = []  # clear after synthesis
    _save_kb(kb)
    return {"ok": True, "nudge": nudge}


# ── Finance: Recurring Bill Templates ─────────────────────────────────────────

@app.get("/api/finance/templates")
def api_get_templates(dlsession: Optional[str] = Cookie(default=None)):
    if not get_session_user(dlsession):
        raise HTTPException(status_code=401, detail="Not logged in")
    kb = load_kb()
    return kb.get("finance", {}).get("bill_templates", [])


@app.post("/api/finance/templates")
async def api_create_template(
    dlsession: Optional[str] = Cookie(default=None),
    body: dict = Body(...),
):
    uid = get_session_user(dlsession)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    kb = load_kb()
    admins = kb.get("_meta", {}).get("admins", ["u1"])
    if uid not in admins:
        raise HTTPException(status_code=403, detail="Admin access required")
    template = {
        "id":               f"tmpl_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "name":             body.get("name", "Bill"),
        "category":         body.get("category", "utility"),
        "amount_inr":       float(body.get("amount_inr", 0)),
        "frequency":        body.get("frequency", "monthly"),
        "included_rooms":   body.get("included_rooms", []),
        "last_logged_date": None,
        "next_due_date":    None,
        "notes":            body.get("notes", ""),
    }
    kb["finance"].setdefault("bill_templates", []).append(template)
    _save_kb(kb)
    return {"ok": True, "template": template}


@app.post("/api/finance/templates/{template_id}/log")
async def api_log_template(
    template_id: str,
    dlsession: Optional[str] = Cookie(default=None),
):
    uid = get_session_user(dlsession)
    if not uid:
        raise HTTPException(status_code=401, detail="Not logged in")
    kb = load_kb()
    admins = kb.get("_meta", {}).get("admins", ["u1"])
    if uid not in admins:
        raise HTTPException(status_code=403, detail="Admin access required")

    templates = kb.get("finance", {}).get("bill_templates", [])
    template = next((t for t in templates if t["id"] == template_id), None)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    amount = template["amount_inr"]
    included_rooms = template.get("included_rooms", [])
    rooms_map = {r["id"]: r for r in kb.get("rooms", [])}
    residents_map = {r["id"]: r for r in kb.get("residents", [])}

    splits = []
    for room_id in included_rooms:
        room = rooms_map.get(room_id)
        if not room:
            continue
        occ_id = room.get("occupant_id")
        occ_name = residents_map[occ_id]["name"] if occ_id and occ_id in residents_map else "Vacant"
        splits.append({
            "room_id":       room_id,
            "room_name":     room["name"],
            "occupant_id":   occ_id,
            "occupant_name": occ_name,
        })

    if not splits:
        raise HTTPException(status_code=400, detail="No valid rooms in template")

    share = round(amount / len(splits), 2)
    for s in splits:
        s["share_inr"] = share

    method = "direct_split" if amount >= 1000 else "pool_deduction"
    entry = {
        "id":                f"exp_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "date":              datetime.now().strftime("%Y-%m-%d"),
        "category":          template["category"],
        "description":       template["name"],
        "amount_inr":        amount,
        "method":            method,
        "num_spaces":        len(splits),
        "share_per_space_inr": share,
        "splits":            splits,
        "logged_by":         uid,
        "from_template":     template_id,
    }
    kb["finance"]["expense_log"].append(entry)

    freq_days = {"monthly": 30, "bimonthly": 60, "quarterly": 90}
    days = freq_days.get(template.get("frequency", "monthly"), 30)
    template["last_logged_date"] = datetime.now().strftime("%Y-%m-%d")
    template["next_due_date"] = (datetime.now() + timedelta(days=days)).strftime("%Y-%m-%d")

    _save_kb(kb)
    return {"ok": True, "entry": entry}
