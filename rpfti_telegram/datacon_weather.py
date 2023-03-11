from .datacon_integr import get_data
from .core_addon import BotCommand, BotAddon
import rpfti.shared_config
from datetime import datetime


def _read_config():
    url = rpfti.shared_config.DATACON_URL
    datasource_id = rpfti.shared_config.DATACON_DATASOURCE_ID
    tag_name = rpfti.shared_config.DATACON_TAG_NAME
    return url, datasource_id, tag_name


# Tags is a list of dicts with keys "datasource_id" and "name"
def _request_current_temperature(url, tags):
    request = {
                "tags": tags,
                "depth": 1,
                "only_valid": True,
                "round_numerics": 2,
                "get_limits": 1,
                "diag_info": False,
                "get_trends": [
                 10800,
                 86400
                ]
            }
    return get_data(url, request, True)


def _parse_temperature_response(response):
    reports = []
    if response["status"] == "ERROR":
        reports.append("Что-то пошло не так")
    else:
        for tag in response["payload"]["tags"]:
            name = tag["display_name"]
            current_reading = tag["readings"][0]
            current_value = current_reading["reading"]
            units = tag["units"]
            timestamp_str = current_reading["timestamp_receive"]
            if ":" == timestamp_str[-3:-2]:
                timestamp_str = timestamp_str[:-3] + timestamp_str[-2:]
            if "Z" == timestamp_str[-1]:
                timestamp = datetime.\
                    strptime(current_reading["timestamp_receive"][:-1],
                             "%Y-%m-%dT%H:%M:%S.%f")
            else:
                timestamp = datetime.\
                    strptime(current_reading["timestamp_receive"],
                             "%Y-%m-%dT%H:%M:%S.%f%z")
            report = "{}: {}{}".format(name, current_value, units)
            freshness = (datetime.utcnow() - timestamp).total_seconds()
            if freshness > 3600:
                report += "\nДанные обновлены более часа назад"
                " и являются тухлыми. Обратитесь к телемастеру."
            else:
                trend_value = None
                trend_direction = None
                day_avg = None
                for t in current_reading["trends"]:
                    if t["period_seconds"] == 10800 and "direction" in t:
                        if t["direction"] != "stable":
                            trend_value = abs(round(t["slope"] * 3600, 2))
                            if t["direction"] == "increase":
                                trend_direction = "Растёт"
                            elif t["direction"] == "decrease":
                                trend_direction = "Падает"
                    elif t["period_seconds"] == 86400 and "average" in t:
                        day_avg = round(t["average"]["reading"], 2)
                if trend_value is not None:
                    report += "\n{} на {}{} в час (за последние 3 часа)".\
                        format(trend_direction, trend_value, units)
                if day_avg is not None:
                    report += "\nСреднее значение за сутки: {}{}".\
                        format(day_avg, units)
            reports.append(report)
    return reports


def get_weather(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    url, datasource_id, tag_name = _read_config()
    weather_data = _request_current_temperature(
        url,
        [
            {
                "datasource_id": datasource_id,
                "name": tag_name
            }
        ]
    )
    reports = _parse_temperature_response(weather_data)
    for r in reports:
        print("SENDING MESSAGE")
        bot.send_message(chat, r, origin_user=user,
                         reply_to=message.message_id)


def cmd_weather():
    return BotCommand("weather_nn", get_weather,
                      help_text="температура за окном")


def make_weather_addon():
    return BotAddon("Weather", "погода за окном",
                    [cmd_weather()])
