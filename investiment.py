import os, time, math
import datetime as dt
import pytz, requests, yfinance as yf

TICKER_USA = "NVDA"
TICKER_BDR = "NVDC34.SA"

INTERVALO_ALERTAS = 65      # segundos/seconds
HEARTBEAT_CICLOS = 5

APORTE_MENSAL = 0 # coloque o valor/insert the value
DIA_UTIL_DCA = 5

ALERTA_QUEDA_FRACA = -0.02
ALERTA_QUEDA_FORTE = -0.05
ALERTA_QUEDA_CRASH = -0.10
ALERTA_ALTA_FORTE =  0.05
ALERTA_ALTA_MUITO_FORTE =  0.10

SEND_EVERY_CYCLE = False
SEND_ON_PRICE_CHANGE = True
PRICE_ABS_TOLERANCE = 0.01    # R$ 0,01
PRICE_PCT_TOLERANCE = 0.0005  # 0,05%

B3_OPEN_HOUR = 10
B3_CLOSE_HOUR = 18   

TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
TELEGRAM_CHAT = os.getenv("CHAT_ID")

def checkTelegram():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("BOT_TOKEN ausente.")
    r1 = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getMe", timeout=10)
    print("[getMe]", r1.status_code, r1.text)
    if TELEGRAM_CHAT:
        r2 = requests.get(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getChat",
                          params={"chat_id": TELEGRAM_CHAT}, timeout=10)
        print("[getChat]", r2.status_code, r2.text)

def isBusinessDay(d: dt.date) -> bool:
    return d.weekday() < 5  

def nthBusinessDayOfMonth(d: dt.date, n: int = 5) -> dt.date:
    d0 = d.replace(day=1)
    count = 0
    while True:
        if isBusinessDay(d0):
            count += 1
            if count == n:
                return d0
        d0 += dt.timedelta(days=1)

def is_b3_open(now_sp: dt.datetime) -> bool:
    if not isBusinessDay(now_sp.date()):
        return False
    return B3_OPEN_HOUR <= now_sp.hour < B3_CLOSE_HOUR

def sendMsg(msg:str) -> None:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        print("Telegram não configurado (BOT_TOKEN/CHAT_ID).")
        return
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT, "text": msg}
    try:
        r = requests.post(url, json=payload, timeout=10)
        if r.status_code != 200:
            print(f"Telegram HTTP {r.status_code}: {r.text}")
    except Exception as e:
        print(f"sendMsg: {e}")

def getNvdaBRL() -> tuple[float, float, str]:
    try:
        t_bdr = yf.Ticker(TICKER_BDR)
        fi = getattr(t_bdr, "fast_info", None)
        if fi and fi.get("last_price") and fi.get("previous_close"):
            last = float(fi["last_price"])
            prev = float(fi["previous_close"])
            change = (last - prev) / prev if prev else 0.0
            return last, change, "BDR (fast_info)"
        h = t_bdr.history(period="1d", interval="1m")
        if not h.empty:
            last = float(h["Close"].iloc[-1])
            d = t_bdr.history(period="5d")
            prev = float(d["Close"].iloc[-2]) if len(d) >= 2 else float(d["Close"].iloc[-1])
            change = (last - prev) / prev if prev else 0.0
            return last, change, "BDR (1m)"
    except Exception:
        pass

    t_us = yf.Ticker(TICKER_USA)
    usd_last = usd_prev = None
    fi_us = getattr(t_us, "fast_info", None)
    if fi_us and fi_us.get("last_price") and fi_us.get("previous_close"):
        usd_last = float(fi_us["last_price"])
        usd_prev = float(fi_us["previous_close"])
    else:
        h_us = t_us.history(period="1d", interval="1m")
        if not h_us.empty:
            usd_last = float(h_us["Close"].iloc[-1])
            d_us = t_us.history(period="5d")
            usd_prev = float(d_us["Close"].iloc[-2]) if len(d_us) >= 2 else float(d_us["Close"].iloc[-1])

    t_fx = yf.Ticker("BRL=X")
    fx_last = fx_prev = None
    fi_fx = getattr(t_fx, "fast_info", None)
    if fi_fx and fi_fx.get("last_price") and fi_fx.get("previous_close"):
        fx_last = float(fi_fx["last_price"])
        fx_prev = float(fi_fx["previous_close"])
    else:
        h_fx = t_fx.history(period="1d", interval="1m")
        if not h_fx.empty:
            fx_last = float(h_fx["Close"].iloc[-1])
            d_fx = t_fx.history(period="5d")
            fx_prev = float(d_fx["Close"].iloc[-2]) if len(d_fx) >= 2 else float(d_fx["Close"].iloc[-1])

    if not (usd_last and usd_prev and fx_last and fx_prev):
        usd_series = t_us.history(period="2d")["Close"]
        fx_series  = t_fx.history(period="2d")["Close"]
        usd_last = float(usd_series.iloc[-1]); usd_prev = float(usd_series.iloc[-2])
        fx_last  = float(fx_series.iloc[-1]);  fx_prev  = float(fx_series.iloc[-2])

    brl_last = usd_last * fx_last
    brl_prev = usd_prev * fx_prev
    brl_bdr_equivalente = brl_last / 6
    change   = (brl_last - brl_prev) / brl_prev if brl_prev else 0.0
    return brl_bdr_equivalente, change, "USD*BRL (intraday, 1/6 BDR)"

def get_daily_ohlc_brl() -> tuple[float,float,float,float,str]:
    try:
        d = yf.Ticker(TICKER_BDR).history(period="2d", interval="1d")
        if not d.empty:
            row = d.iloc[-1]  
            o = float(row["Open"]); h = float(row["High"])
            l = float(row["Low"]);  c = float(row["Close"])
            return o, h, l, c, "BDR (1d)"
    except Exception:
        pass

    t_us = yf.Ticker(TICKER_USA).history(period="2d", interval="1d")
    t_fx = yf.Ticker("BRL=X").history(period="2d", interval="1d")
    if not t_us.empty and not t_fx.empty:
        us = t_us.iloc[-1]; fx = t_fx.iloc[-1]
        o = float(us["Open"] * fx["Open"])
        h = float(us["High"] * fx["High"])
        l = float(us["Low"]  * fx["Low"])
        c = float(us["Close"]* fx["Close"])
        return o, h, l, c, "USD*BRL (1d)"
    raise RuntimeError("Sem OHLC diário disponível ainda.")

def formatPct(x: float) -> str:
    return f"{x*100:+.2f}%"

def alertMsg(price_brl: float, daily_change: float, fonte: str) -> str:
    base = f"NVDC34 {fonte}\nPreço: R$ {price_brl:,.2f}\nDia: {formatPct(daily_change)}"
    if daily_change <= ALERTA_QUEDA_CRASH:
        return f"🚨 CRASH DETECTADO!\n{base}"
    if daily_change <= ALERTA_QUEDA_FORTE:
        return f"⚠️ Queda FORTE!\n{base}"
    if daily_change <= ALERTA_QUEDA_FRACA:
        return f"🔻 Queda no dia.\n{base}"
    if daily_change >= ALERTA_ALTA_MUITO_FORTE:
        return f"📈💸 Alta MUITO forte!\n{base}"
    if daily_change >= ALERTA_ALTA_FORTE:
        return f"📈 Alta forte!\n{base}"
    return f"ℹ️ Atualização\n{base}"

def maybeSendDCASuggestion(price_brl: float) -> None:
    hoje = dt.date.today()
    alvo = nthBusinessDayOfMonth(hoje, DIA_UTIL_DCA)
    if hoje == alvo:
        qtd = math.floor(APORTE_MENSAL / price_brl) or 0
        msg = ("📅 DCA hoje (5º dia útil)\n"
               f"Orçamento: R$ {APORTE_MENSAL:,.2f}\n"
               f"Preço: R$ {price_brl:,.2f}\n"
               f"Sugestão: comprar {qtd} NVDA BDR")
        sendMsg(msg)

def price_changed_enough(curr: float, last_sent: float|None) -> bool:
    if last_sent is None:
        return True
    abs_diff = abs(curr - last_sent)
    pct_diff = abs_diff / last_sent if last_sent else 0.0
    return (abs_diff >= PRICE_ABS_TOLERANCE) or (pct_diff >= PRICE_PCT_TOLERANCE)

def main():
    tz = pytz.timezone("America/Sao_Paulo")
    checkTelegram()
    sendMsg("JBotInvest iniciado. Vou te enviar atualizações periódicas (intraday, alertas por variação e resumo no fechamento) sobre as ações da NVIDIA! 😁")

    last_bucket = None
    ciclos_desde_envio = 0
    last_price_sent = None

    prev_market_open = None
    last_close_notified_date = None

    while True:
        try:
            now_sp = dt.datetime.now(tz)
            is_open = is_b3_open(now_sp)

            if prev_market_open is True and is_open is False:
                try:
                    o,h,l,c,fonte_ohlc = get_daily_ohlc_brl()
                    var_dia = (c - o) / o if o else 0.0
                    msg = ( "B3 FECHOU\n"
                            f"Abertura: R$ {o:,.2f}\n"
                            f"Fechamento: R$ {c:,.2f} ({formatPct(var_dia)})\n"
                            f"Máx/Mín: R$ {h:,.2f} / R$ {l:,.2f}\n"
                            f"Fonte: {fonte_ohlc}" )
                    sendMsg(msg)
                    last_close_notified_date = now_sp.date()
                except Exception as e:
                    print(f"[WARN] Resumo de fechamento indisponível ainda: {e}")

            if (not is_open) and last_close_notified_date != now_sp.date() and now_sp.hour >= B3_CLOSE_HOUR:
                try:
                    o,h,l,c,fonte_ohlc = get_daily_ohlc_brl()
                    var_dia = (c - o) / o if o else 0.0
                    msg = ( "B3 FECHOU (aviso diário)\n"
                            f"Abertura: R$ {o:,.2f}\n"
                            f"Fechamento: R$ {c:,.2f} ({formatPct(var_dia)})\n"
                            f"Máx/Mín: R$ {h:,.2f} / R$ {l:,.2f}\n"
                            f"Fonte: {fonte_ohlc}" )
                    sendMsg(msg)
                    last_close_notified_date = now_sp.date()
                except Exception as e:
                    print(f"[WARN] Fechamento diário ainda não consolidado: {e}")

            prev_market_open = is_open

            price_brl, daily_change, fonte = getNvdaBRL()

            if daily_change <= ALERTA_QUEDA_CRASH:          
                bucket = "CRASH"
            elif daily_change <= ALERTA_QUEDA_FORTE:        
                bucket = "QUEDA_FORTE"
            elif daily_change <= ALERTA_QUEDA_FRACA:        
                bucket = "QUEDA_FRACA"
            elif daily_change >= ALERTA_ALTA_MUITO_FORTE:   
                bucket = "ALTA_MUITO_FORTE"
            elif daily_change >= ALERTA_ALTA_FORTE:         
                bucket = "ALTA_FORTE"
            else:                                           
                bucket = "NEUTRO"

            stamp = now_sp.strftime("%d/%m %H:%M")
            full_text = f"{alertMsg(price_brl, daily_change, fonte)}\n⏱️ {stamp}"
            lite_text = f"NVDC34 R$ {price_brl:,.2f} | {formatPct(daily_change)} ({fonte})\n⏱️ {stamp}"

            sent = False
            if bucket != last_bucket:
                sendMsg(full_text); sent = True
                last_bucket = bucket
                ciclos_desde_envio = 0
                last_price_sent = price_brl
            else:
                if SEND_EVERY_CYCLE:
                    sendMsg(lite_text); sent = True
                    ciclos_desde_envio = 0
                    last_price_sent = price_brl
                elif SEND_ON_PRICE_CHANGE and price_changed_enough(price_brl, last_price_sent):
                    sendMsg(lite_text); sent = True
                    ciclos_desde_envio = 0
                    last_price_sent = price_brl
                else:
                    ciclos_desde_envio += 1
                    if ciclos_desde_envio >= HEARTBEAT_CICLOS:
                        sendMsg(lite_text); sent = True
                        ciclos_desde_envio = 0
                        last_price_sent = price_brl

            maybeSendDCASuggestion(price_brl)

        except Exception as e:
            print(f"Erro: {e}")

        time.sleep(INTERVALO_ALERTAS)

if __name__ == "__main__":
    main()

