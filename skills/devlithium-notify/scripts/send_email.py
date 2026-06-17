"""
devlithium-notify: send_email.py
Sends email notifications to residents from Devlithium.
Uses Gmail SMTP (free). Credentials stored in data/notify_config.json.

Usage:
  python send_email.py --type daily_digest --subject "🏠 Daily" --body "..." --recipients all
"""
import json, smtplib, argparse, os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date

KB_PATH = os.path.join(os.path.dirname(__file__), "../../../data/house_kb.json")
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../../../data/notify_config.json")

def load_config():
    if not os.path.exists(CONFIG_PATH):
        print("⚠️  notify_config.json not found. Run setup_email.py first.")
        return None
    with open(CONFIG_PATH) as f:
        return json.load(f)

def get_recipients(kb, selection):
    residents = [r for r in kb.get("residents", []) if r.get("role") != "inactive"]
    if selection == "all":
        return [(r["name"], r["email"]) for r in residents if r.get("email")]
    ids = [s.strip() for s in selection.split(",")]
    return [(r["name"], r["email"]) for r in residents if r["id"] in ids and r.get("email")]

def send_email(msg_type, subject, body, recipients_selection):
    config = load_config()
    if not config:
        print("Email not configured. Saving to notification queue instead.")
        queue_notification(msg_type, subject, body, recipients_selection)
        return

    with open(KB_PATH) as f:
        kb = json.load(f)

    recipients = get_recipients(kb, recipients_selection)
    if not recipients:
        print("⚠️  No valid recipients found.")
        return

    sender_email = config.get("gmail_address")
    sender_password = config.get("gmail_app_password")

    try:
        server = smtplib.SMTP_SSL("smtp.gmail.com", 465)
        server.login(sender_email, sender_password)

        for name, email in recipients:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"Devlithium 🏠 <{sender_email}>"
            msg["To"] = email
            personalized_body = body.replace("[name]", name)
            msg.attach(MIMEText(personalized_body, "plain"))
            server.sendmail(sender_email, email, msg.as_string())
            print(f"✅ Sent to {name} ({email})")

        server.quit()
        print(f"📧 {len(recipients)} notification(s) sent | Type: {msg_type}")

    except Exception as e:
        print(f"❌ Email failed: {e}")
        queue_notification(msg_type, subject, body, recipients_selection)

def queue_notification(msg_type, subject, body, recipients):
    """Fallback: save to notification queue file if email not set up."""
    queue_path = os.path.join(os.path.dirname(__file__), "../../../logs/notification_queue.jsonl")
    entry = {
        "date": str(date.today()),
        "type": msg_type,
        "subject": subject,
        "body": body[:200],
        "recipients": recipients,
        "status": "queued"
    }
    with open(queue_path, "a") as f:
        f.write(json.dumps(entry) + "\n")
    print(f"📋 Queued notification: {subject}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--type", default="general")
    parser.add_argument("--subject", required=True)
    parser.add_argument("--body", required=True)
    parser.add_argument("--recipients", default="all")
    args = parser.parse_args()
    send_email(args.type, args.subject, args.body, args.recipients)
