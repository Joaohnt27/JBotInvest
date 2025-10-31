import os, requests

BOT_TOKEN = os.getenv("BOT_TOKEN")
print("len(token)=", 0 if not BOT_TOKEN else len(BOT_TOKEN), "…", BOT_TOKEN[-6:] if BOT_TOKEN else None)

r = requests.get(f"https://api.telegram.org/bot{BOT_TOKEN}/getMe", timeout=10)
print(r.status_code, r.text)
