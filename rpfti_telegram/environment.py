import requests
import rpfti.shared_config
import json
import math
import datetime
import re
from .core_addon import BotCommand, BotAddon

aqi_link = "http://api.airvisual.com/v2/nearest_city?lat={}&lon={}&key={}"

errors = {
    "call_limit_reached": "истёк лимит на запросы",
    "city_not_found": "рядом не найдены города или станции мониторинга",
    "ip_location_failed": "рядом не найдены города или станции мониторинга",
    "no_nearest_station": "рядом не найдены города или станции мониторинга",
    "too_many_requests": "истёк лимит на запросы"
}

# clear sky (day)	01d.png	
# clear sky (night)	01n.png	
# few clouds (day)	02d.png	
# few clouds (night)	02n.png	
# scattered clouds	03d.png	
# broken clouds	04d.png	
# shower rain	09d.png	
# rain (day time)	10d.png	
# rain (night time)	10n.png	
# thunderstorm	11d.png	
# snow	13d.png	
# mist	50d.png

weather_types = {
    "01": "☀️",
    "02": "🌤",
    "03": "🌥",
    "04": "☁️",
    "09": "🌧",
    "10": "🌦",
    "11": "🌩",
    "13": "🌨",
    "50": "🌫"
}

coords_re = re.compile("^\s*(\d+[\.,]?\d*)\D+(\d+[\.,]?\d*)\s*$")

# {
#     "status": "success",
#     "data":
#     {
#         "city": "Inashiki",
#         "state": "Ibaraki",
#         "country": "Japan",
#         "location":
#         {
#             "type": "Point",
#             "coordinates":
#             [
#                 140.32356,
#                 35.95633
#             ]
#         },
#         "current":
#         {
#             "pollution":
#             {
#                 "ts": "2023-03-05T16:00:00.000Z",
#                 "aqius": 21,
#                 "mainus": "p2",
#                 "aqicn": 7,
#                 "maincn": "p2"
#             },
#             "weather":
#             {
#                 "ts": "2023-03-05T16:00:00.000Z",
#                 "tp": 7,
#                 "pr": 1021,
#                 "hu": 72,
#                 "ws": 0.89,
#                 "wd": 90,
#                 "ic": "10n"
#             }
#         }
#     }
# }


def _parse_air(air_response):
    result_string = "Показатели воздуха для выбранных координат:\n\n"
    data = air_response.get("data")
    result_string += "{}, {}\n".format(data.get("country",
                                                "Страна не распознана"),
                                       data.get("city", "Город не распознан"))
    current_data = data.get("current")
    aqius = current_data.get("pollution").get("aqius")
    if aqius <= 50:
        quality = "💙, воздух очень чистый. Гуляй и занимайся спортом на улице."
    elif aqius <= 100:
        quality = "💚, воздух достаточно чистый, но могут быть проблемы" + \
            " у чувствительных людей. Если ты не такой, то ни в чём себя" + \
            " не ограничивай."
    elif aqius <= 150:
        quality = "💛, качество воздуха среднее, может вызвать проблемы" + \
            " со здоровьем у части людей. Рекомендуется избегать" + \
            " физических нагрузок на открытом воздухе."
    elif aqius <= 200:
        quality = "😷, воздух грязный и может вызвать проблемы со" + \
            " здоровьем, у чувствительных людей — серьёзные." + \
            " По возможности ограничь пребывание на улице или надевай маску."
    elif aqius <= 300:
        quality = "😵, воздух очень грязный и может быть опасен для" + \
            " здоровья даже здоровых людей. Сиди дома или надевай респиратор."
    else:
        quality = "☠️, воздух чрезвычайно грязный, весьма опасен для" + \
            " здоровья, даже не думай выходить на улицу без" + \
            " очень серьёзной защиты, а дома не открывай даже форточки."
    result_string += "Качество воздуха: {} {}\n".format(aqius, quality)
    weather_type_raw = current_data.get("weather").get("ic")[:2]
    weather_type = weather_types.get(weather_type_raw)
    result_string += "\nПогода:\n"
    if weather_type:
        result_string += "{} ".format(weather_type)
    result_string += "{}°C, влажность {}%, давление {:.1f} мм рт. ст.\n".format(
                        current_data.get("weather").get("tp"),
                        current_data.get("weather").get("hu"),
                        current_data.get("weather").get("pr") * 0.7500637554
    )
    wind_dir = current_data.get("weather").get("wd")
    if wind_dir >= 337.5 or wind_dir <= 22.5:
        direction = "северный"
    elif wind_dir > 22.5 and wind_dir <= 67.5:
        direction = "северный-восточный"
    elif wind_dir > 67.5 and wind_dir <= 112.5:
        direction = "восточный"
    elif wind_dir > 112.5 and wind_dir <= 157.5:
        direction = "юго-восточный"
    elif wind_dir > 157.5 and wind_dir <= 202.5:
        direction = "южный"
    elif wind_dir > 202.5 and wind_dir <= 247.5:
        direction = "юго-западный"
    elif wind_dir > 247.5 and wind_dir <= 292.5:
        direction = "западный"
    else:
        direction = "северо-западный"
    result_string += "Ветер {}, {} м/с".format(direction,
                                               current_data.get("weather").get("ws"))
    return result_string


def air(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    txt = "Чтобы узнать данные о воздухе вокруг тебя, пришли свою геолокацию"
    all_sent = bot.send_message(chat, txt, origin_user=user,
                                reply_to=message.message_id)
    context = {
        "command": "air",
        "action": "request_reply"
    }
    for a in all_sent:
        bot.keep_context(cmd.addon, context, a.message_id)


def air_reply_handler(addon, db_context, context, user, chat, message):
    bot = addon.bot
    result_txt = "Не удалось выполнить команду"
    coords = None
    if context.get("command") == "air":
        if message.location:
            coords = (float(message.location.latitude),
                      float(message.location.longitude))
        elif message.text:
            coords_match = coords_re.search(message.text)
            if coords_match:
                coords = (float(coords_match.group(1).replace(",", ".")),
                          float(coords_match.group(2).replace(",", ".")))
            else:
                result_txt = "Не могу разобрать координаты"
        elif message.photo:
            result_txt = "😳"
        else:
            result_txt = "Пришли координаты текстом или геолокацией"
    if coords:
        r = requests.get(aqi_link.format(coords[0], coords[1],
                                         rpfti.shared_config.AQI))
        status = r.json().get("status")
        if status != "success":
            result_txt = "Не удалось получить данные по координатам " + \
                "{}, {} — сервис сообщил, что {}".format(
                    coords[0], coords[1],
                    errors.get(r.json().get("data").get("message"),
                               "что-то сломалось"))
        else:
            result_txt = _parse_air(r.json())
    bot.send_message(chat, result_txt, origin_user=user,
                     reply_to=message.message_id)


def cmd_air():
    return BotCommand("air", air, help_text="узнать состояние воздуха")


def make_air_addon():
    return BotAddon("Environment", "запросы данных по координатам",
                    [cmd_air()], reply_handler=air_reply_handler)