import requests, json, datetime
from .core_addon import BotCommand, BotAddon

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

# Currencies is a list of dicts:
# display - display name (or flag)
# code - three-letter code of currency
def _get_currencies(all_results, currencies):
    result_string = ""
    if all_results["status"] != "OK":
        return "Что-то пошло не так"
    timestamp_str = all_results["Timestamp"]
    if ":" == timestamp_str[-3:-2]:
        timestamp_str = timestamp_str[:-3] + timestamp_str[-2:]
    timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%dT%H:%M:%S%z")
    result_string += "Данные на {}:".format(timestamp.strftime("%d.%m.%Y"))
    for curr in currencies:
        code = curr["code"]
        logo = curr["display"]
        if code in all_results["Valute"]:
            nominal = all_results["Valute"][code]["Nominal"]
            current = all_results["Valute"][code]["Value"]
            previous = all_results["Valute"][code]["Previous"]
            name = all_results["Valute"][code]["Name"]
            diff = current - previous
            result_string += "\n{} {} {}: {} руб.".format(logo, nominal, name, current)
            if diff > 0:
                result_string += " (🔺{})".format(round(diff,4))
            elif diff < 0:
                result_string += " (🔻{})".format(round(diff,4))
            else:
                result_string += " (не менялся)"
    return result_string

def get_usd_eur(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    currencies = _get_currencies_all()
    txt = _get_currencies(currencies, [
        {
            "code": "USD",
            "display": "🇺🇸"
        },
        {
            "code": "EUR",
            "display": "🇪🇺"
        },
        {
            "code": "RON",
            "display": "🇹🇩"
        }
    ])
    bot.send_message(chat, txt, origin_user=user,
                    reply_to=message.message_id)

cmd_usd_eur = BotCommand(
    "currencies", get_usd_eur, help_text="Текущий курс основных валют к рублю ЦБ РФ")

cbrf_addon = BotAddon("CBRF", "курсы валют ЦБ РФ",
                        [cmd_usd_eur])