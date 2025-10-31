# 🤖 JBotInvest

A Telegram Bot that monitors NVIDIA’s stocks at B3 in real time.

---
# 🔍 Overview

JBotInvest is a Python-based Telegram bot designed to track NVIDIA stock prices on the Brazilian market (B3), send real-time alerts, daily summaries, and DCA suggestions directly to your Telegram chat.

It uses Yahoo Finance data (yfinance) and automatically converts prices to BRL, including a fallback mode using *NVDA × USD/BRL* if BDR data is unavailable.

---
# 1️⃣ Create the bot at Telegram:
1. At telegram, search for user: @BotFather;
2. Send the command: ```/newbot```
3. Choose one name and a unique @username (ex:@JBotInvest_bot);
4. BotFather will reply with an API token, like this: ``` 1234567890:ABCDefGhIJKlmNoPQrstUVwxyZ ```
5. Copy this token (you will use it later in your code).

# 2️⃣ Get the chat ID:
1. Send any message to your new bot (Example: Hi!);
2. Open this URL in your browser: https://api.telegram.org/botYOUR_TOKEN/getUpdates
   - (Change "YOUR_TOKEN" for that you copy from BotFather)
3. In the JSON's response, look for something like:
   ```bash
   "chat": { "id": 123456789, "first_name": "João", ... }
   ```
   This number is your CHAT_ID.

# 3️⃣ Set environment variables (Windowns PowerShell):
Avoid insert the token directly at your code (for security reasons).
At PowerShell, execute: 
```bash
setx BOT_TOKEN "1234567890:ABCDefGhIJKlmNoPQrstUVwxyZ"
setx CHAT_ID "123456789"
```
Then restart the terminal to apply.
You can check with:
```bash
echo $env:BOT_TOKEN
echo $env:CHAT_ID
```

# 4️⃣ Install dependencies:
Run in PowerShell or VS Code terminal: 
```bash
pip install yfinance requests pytz
```
---
# ⚙️ How it works

# 🔁 Main loop:
At each INTERVALO_ALERTAS (alert interval, in seconds), the bot:

- Fetches the latest NVIDIA price (NVDC34 or NVDA×BRL fallback);
- Calculates the daily percentage change;
- Sends alerts for strong movements;
- Posts periodic updates (heartbeat);
- Checks for DCA (5th business day).

# 💬 Alerts:
| Type            | Condition | Message                 |
| --------------- | --------- | ----------------------- |
| ⚠️ Mild drop    | ≤ −2%     | “Price down today.”     |
| 🚨 Strong drop  | ≤ −5%     | “Strong fall detected!” |
| 💥 Crash        | ≤ −10%    | “CRASH DETECTED!”       |
| 📈 Strong rise  | ≥ +5%     | “Strong rise!”          |
| 💸 Extreme rise | ≥ +10%    | “Huge rally!”           |

# 🕒 Market Closing: 
When the market closes (after 18:00h BRT):
- Show open and close values of the day;
- Informs the final variation.
