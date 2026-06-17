---
name: devlithium-inventory
description: Use this skill for all grocery and household inventory management in the Devlithium home. Triggers when the user says "check inventory", "we're out of X", "reorder groceries", "update stock", "what do we need", "grocery list", "log that we bought X", or any inventory-related request. Also triggers when the daily check identifies items below reorder threshold. Always prefers the cheapest available delivery option.
---

# devlithium-inventory

Manages grocery and supplies inventory for the house. Tracks quantities, triggers reorders, and logs all purchases to the finance module.

**Model rule**: This is a Haiku task. Load only `house_kb.inventory` — not the full KB.

## Data
- Read/Write: `house_kb.json` → `inventory` section only
- Expense log: `house_kb.json` → `finance.expense_log`

---

## Check Inventory
Run when daily check calls this module OR user asks "what do we need".

```bash
python skills/devlithium-inventory/scripts/check_inventory.py
```

Output format:
```
🛒 INVENTORY STATUS — [date]
🔴 CRITICAL (qty = 0): [items]
🟡 LOW (qty ≤ threshold): [items]
🟢 OK: [N items]

Suggested order: [items + quantities]
Estimated cost: ₹[amount]
```

## Log a Purchase
When a resident says they bought something or an order was delivered:
```bash
python skills/devlithium-inventory/scripts/update_inventory.py \
  --item "Milk" --qty 3 --unit "liters" --cost 150 --buyer "u1"
```
This updates `current_qty` AND logs to `finance.expense_log`.

## Trigger Reorder
For items with `auto_order: true`:
1. Check which delivery app is preferred for that item
2. Generate the order details (item, qty, estimated cost)
3. **If cost ≤ ₹500**: prepare order details, notify resident with one-tap confirm link
4. **If cost > ₹500**: require explicit resident approval first
5. Log order attempt to daily_log

For items with `auto_order: false`:
- Add to next notification digest as "needs reorder"
- Don't order autonomously

## Add New Item to Inventory
When user says "also track [item]":
1. Ask: unit, typical weekly consumption, reorder threshold, preferred supplier
2. Append to `house_kb.inventory.grocery` or `cleaning_supplies`
3. Confirm: "Added [item] to tracking. Reorder alert when qty drops below [threshold]."

## Delivery App Priority (Jaipur)
1. **Blinkit** — fastest (10 min), slightly premium
2. **Zepto** — fast (15 min), competitive pricing
3. **Swiggy Instamart** — good variety
4. **Local sabzi mandi** — cheapest for vegetables, no delivery
5. **Country Delight / Delight** — milk subscription (auto-daily)

Always note: Devlithium doesn't place orders autonomously yet (Phase 2). In Phase 1, it generates the order list and notifies the resident to place it.

---

## Terrace Farm Offset
If `sustainability.terrace_farm.active == true`:
- Check `crops` for items ready to harvest
- Subtract harvested qty from reorder need
- Log savings to sustainability tracker

---

## Output on any inventory action
Always end with:
```
📦 Updated: [item] | New qty: [X] | Next reorder at: [threshold]
💰 Cost logged: ₹[amount] | Pool fund balance: ₹[balance]
```
