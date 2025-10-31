# 🤖 JBotInvest

A Telegram Bot that monitors NVIDIA’s stocks at B3 in real time.

---
# 🔍 Overview

JBotInvest is a Python-based Telegram bot designed to track NVIDIA stock prices on the Brazilian market (B3), send real-time alerts, daily summaries, and DCA suggestions directly to your Telegram chat.

It uses Yahoo Finance data (yfinance) and automatically converts prices to BRL, including a fallback mode using *NVDA × USD/BRL* if BDR data is unavailable.

---
# 1️⃣ Create the bot at Telegram:
1. At telegram, search for user: @BotFather;
2. Send the command: /newbot;
3. Choose one name and @username exclusive (ex:@JBotInvest_bot);
4. BotFather will awnser you with a message that contains your API's token, at this format: ``` 1234567890:ABCDefGhIJKlmNoPQrstUVwxyZ ```
5. Copy this token (he will be used in code).

# 2️⃣ Get the chat ID:
1. Send any message to your new bot (ex: Hi!);
2. Open your browser at this URL: https://api.telegram.org/botYOUR_TOKEN/getUpdates
   - (Change "YOUR_TOKEN" for that you copy from BotFather)
3. At the JSON's awnser, seach for something like this:
   ```bash
   "chat": { "id": 123456789, "first_name": "João", ... }
   ```
   This number is your CHAT_ID.

# 3️⃣ Define environment variables at Windowns PowerShell:
Avoid insert the token directly at your code (for security reasons).
At PowerShell, execute: 
```bash
setx BOT_TOKEN "1234567890:ABCDefGhIJKlmNoPQrstUVwxyZ"
setx CHAT_ID "123456789"
```
Close and open the terminal to apply.
You can check with:
```bash
echo $env:BOT_TOKEN
echo $env:CHAT_ID
```

# 4️⃣ Install dependencies:
Execute a PowerShell or at VSCode terminal: 
```bash
pip install yfinance requests pytz
```
---

# How does the bot works
# 🔁 Main loop:
At each INTERVALO_ALERTAS (alert interval) seconds:
- Search for actual stock's price;
- Calculate the percentual variation of the day;
- Decides if send alert (fall/high);
- Send periodic updates (heartbeat);
- Check if it is day of DCA.

# 💬 Alerts:
| Type            | Condition | Message             |
| --------------- | --------- | ------------------- |
| ⚠️ Queda leve   | ≤ -2%    | “Queda no dia.”     |
| 🚨 Queda forte  | ≤ -5%    | “Queda FORTE!”      |
| 💥 Crash        | ≤ -10%   | “CRASH DETECTADO!”  |
| 📈 Alta forte   | ≥ +5%    | “Alta forte!”       |
| 💸 Alta extrema | ≥ +10%   | “Alta MUITO forte!” |

# 🕒 Closing: 
When the market closes (after 18:00h BRT):
- Show open and close values of the day;
- Informs the final variation.
