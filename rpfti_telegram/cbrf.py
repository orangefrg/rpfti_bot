import requests
import json
import math
import datetime
import lxml.html as html
from .core_addon import BotCommand, BotAddon

BINANCE_SYMBOLS = [
    ("Bitcoin к USDT", "BTCUSDT", "USD"),
    ("Ethereum к USDT", "ETHUSDT", "USD"),
    ("BNB к USDT", "BNBUSDT", "USD"),
    ("Ripple к USDT", "XRPUSDT", "USD"),
    ("Dogecoin к USDT", "DOGEUSDT", "USD")
    ]

link_moex = "https://iss.moex.com/iss/statistics/engines/futures/markets/indicativerates/securities"

def _get_currencies_all():
    r = requests.get("https://www.cbr-xml-daily.ru/daily_json.js")
    if r.status_code != 200:
        return {
            "status": "ERROR",
            "code": r.status_code
        }
    else:
        result = json.loads(r.text)
        result["status"] = "OK"
        return result


def _get_currencies_moex():
    r = requests.get(link_moex)
    doc = html.document_fromstring(r.content)
    rows = doc.findall(".//row")
    moex_result = {}
    for row in rows:
        moex_result[row.get("secid")] = {
            "rate": float(row.get("rate") or 0),
            "tradedate": row.get("tradedate"),
            "tradetime": row.get("tradetime")
        }
    return moex_result


# Currencies is a list of dicts:
# display - display name (or flag)
# code - three-letter code of currency
def _get_currencies(all_results, currencies, moex=None):
    result_string = ""
    if all_results["status"] != "OK":
        return "Что-то пошло не так"
    timestamp_str = all_results["Timestamp"]
    if ":" == timestamp_str[-3:-2]:
        timestamp_str = timestamp_str[:-3] + timestamp_str[-2:]
    timestamp = datetime.datetime.strptime(timestamp_str,
                                           "%Y-%m-%dT%H:%M:%S%z")
    result_string += "Данные на {}:".format(timestamp.strftime("%d.%m.%Y"))
    for curr in currencies:
        code = curr["code"]
        logo = curr["display"]
        nominal = 1
        if code in all_results["Valute"]:
            nominal = all_results["Valute"][code]["Nominal"]
            current = all_results["Valute"][code]["Value"]
            previous = all_results["Valute"][code]["Previous"]
            name = all_results["Valute"][code]["Name"]
            diff = current - previous
            result_string += "\n{} {} {}: {} ₽".format(logo,
                                                       nominal,
                                                       name,
                                                       current)
            if diff > 0:
                result_string += " (🔺{})".format(round(diff, 4))
            elif diff < 0:
                result_string += " (🔻{})".format(round(diff, 4))
            else:
                result_string += " (не менялся)"
        else:
            result_string += "\n{} Курс не установлен".format(logo)
        moex_res = moex.get("{}/RUB".format(curr["code"]))
        if moex_res:
            result_string += ", биржевой курс на {} {} — {:.4f} ₽".format(
                moex_res["tradedate"],
                moex_res["tradetime"],
                moex_res["rate"] * nominal)
    return result_string


def get_usd_eur(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    cb_results = _get_currencies_all()
    moex_results = _get_currencies_moex()
    txt = _get_currencies(cb_results, [
        {
            "code": "USD",
            "display": "🇺🇸"
        },
        {
            "code": "EUR",
            "display": "🇪🇺"
        },
        {
            "code": "CNY",
            "display": "🇨🇳"
        },
        {
            "code": "TRY",
            "display": "🇹🇷"
        },
        {
            "code": "GEL",
            "display": "🇬🇪"
        },
        {
            "code": "KZT",
            "display": "🇰🇿"
        },
        {
            "code": "AMD",
            "display": "🇦🇲"
        },
        {
            "code": "UZS",
            "display": "🇺🇿"
        },
        {
            "code": "THB",
            "display": "🇹🇭"
        },
        {
            "code": "RSD",
            "display": "🇷🇸"
        }
    ], moex_results)
    bot.send_message(chat, txt, origin_user=user,
                     reply_to=message.message_id)


def get_crypto(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    moex_results = _get_currencies_moex()
    result_string = "Средние курсы криптовалют на Binance за последние 5 минут:\n\n"
    for cc in BINANCE_SYMBOLS:
        price = requests.get(
            "https://data.binance.com"
            "/api/v3/avgPrice?symbol={}".format(cc[1])).json().get("price")
        if price is not None:
            fprice = float(price or 0)
            result_string += "{} — {:.4f}".format(cc[0], fprice)
            moex_cur = moex_results.get("{}/RUB".format(cc[2]))
            if moex_cur:
                result_string += " ({:.2f} ₽ по биржевому курсу)".format(
                    moex_cur["rate"] * fprice)
        else:
            result_string += "Не удалось получить для пары {}".format(cc[0])
        result_string += "\n"
    bot.send_message(chat, result_string, origin_user=user,
                     reply_to=message.message_id)


def cmd_usd_eur():
    return BotCommand("currencies",
                      get_usd_eur,
                      help_text="Текущий курс основных валют к рублю ЦБ РФ")


def cmd_crypto():
    return BotCommand("crypto",
                      get_crypto,
                      help_text="Текущий курс основных криптовалют на Binance")


def make_cbrf_addon():
    return BotAddon("CBRF", "курсы валют",
                    [cmd_usd_eur(), cmd_crypto()])
                    