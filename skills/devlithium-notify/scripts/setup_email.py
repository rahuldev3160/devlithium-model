"""
devlithium-notify: setup_email.py
One-time setup for Gmail SMTP credentials.
Stores config in data/notify_config.json (never committed to git).
"""
import json, os, getpass

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "../../../data/notify_config.json")

def setup():
    print("=== Devlithium Email Setup ===")
    print("Uses Gmail SMTP (free). Requires a Gmail App Password.")
    print("Get one at: https://myaccount.google.com/apppasswords\n")

    gmail = input("Enter your Gmail address (sender): ").strip()
    password = getpass.getpass("Enter Gmail App Password (hidden): ").strip()

    config = {}
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH) as f:
            config = json.load(f)

    config["gmail_address"] = gmail
    config["gmail_app_password"] = password
    config["whatsapp_enabled"] = config.get("whatsapp_enabled", False)
    config["twilio_sid"] = config.get("twilio_sid", None)
    config["twilio_token"] = config.get("twilio_token", None)
    config["twilio_whatsapp_from"] = config.get("twilio_whatsapp_from", None)

    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        json.dump(config, f, indent=2)

    # Add to .gitignore
    gitignore = os.path.join(os.path.dirname(__file__), "../../../.gitignore")
    with open(gitignore, "a") as f:
        f.write("\ndata/notify_config.json\n")

    print(f"\n✅ Email configured for {gmail}")
    print("🔒 notify_config.json added to .gitignore (credentials are local only)")
    print("\nTest it: python send_email.py --type test --subject 'Devlithium Test' --body 'Hello from Devlithium!' --recipients u1")

if __name__ == "__main__":
    setup()
