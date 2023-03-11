from .core_addon import BotCommand, BotAddon
import datetime


def get_summary(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    bots = bot.models["Bots"]
    messages = bot.models["Messages"]

    out_string = "Краткая сводка по боту\n"

    for b in bots.objects.all():
        totaltime = datetime.datetime.utcnow() - b.\
            start_time.replace(tzinfo=None)
        out_string += "Бот {} (запущен {}, работает {})"\
            ", в статистике {} сообщений\n".format(
                b.name, b.start_time, totaltime,
                messages.objects.filter(bot=b).count())
    pass


def get_statistics(cmd, user, chat, message, cmd_args):
    text = "Запрос полной статистики..."
    cmd.addon.bot.send_message(chat, origin_user=user, text=text,
                               reply_to=message.message_id)
    bot = cmd.addon.bot
    bots = bot.models["Bots"]
    chats = bot.models["Chats"]
    users = bot.models["Users"]
    messages = bot.models["Messages"]
    likes = bot.models["Likes"]
    tasks = bot.models["Tasks"]
    out_string = "Полная статистика\n\n"

    for b in bots.objects.all():
        totaltime = datetime.datetime.utcnow() - \
            b.start_time.replace(tzinfo=None)
        out_string += "---Бот {}---\n(запущен {}, работает {})\n".format(
            b.name, b.start_time, totaltime)
        out_string += "ЧАТЫ:\n"
        for c in chats.objects.filter(bot=b):
            if c.chat_type in ["group", "supergroup"]:
                out_string += "👨‍👩‍👧‍👦 Чат \"{}\"".format(c.title)
            elif c.chat_type == "channel":
                out_string += "🗣 Канал \"{}\"".format(c.title)
            elif c.chat_type == "private":
                out_string += "👨🏻 Личные сообщения с {} {} {}".format(
                    c.first_name, c.user_name, c.last_name)
            else:
                out_string += "Неизвестный тип диалога: {}".format(
                    c.telegram_id)
            out_string += " (добавлен {})".format(c.init_date)
            if c.is_active:
                out_string += " и сейчас активен,\n|"
            else:
                out_string += " и сейчас отключен,\n|"
            out_string += "|\tвсего {} сообщений\n|\n|".format(
                messages.objects.filter(chat=c, bot=b).count())
            for t in tasks.objects.filter(chat=c, bot=b):
                out_string += \
                    "|\t⏰ Задача: аддон "
                "{}, команда {}, сработает в {} (уже срабатывала {} раз)\n".\
                    format(t.addon, t.command, t.trigger_time, t.counter)
            out_string += "---\n"
        out_string += "\nПользователи:\n"
        for u in users.objects.filter(bot=b):
            out_string += "{} {} {} - {},".format(
                u.first_name, u.user_name, u.last_name,
                messages.objects.filter(to_user=u).count())
            out_string += " понравилось {} сообщений\n".format(
                likes.objects.filter(liked_by=u).count())

        out_string += "\n\n"
    cmd.addon.bot.send_message(chat, origin_user=user, text=out_string,
                               reply_to=message.message_id)


def cmd_get_stats():
    return BotCommand("get_stats", get_statistics,
                      help_text="запрос статистики",
                      acceptable_roles=["ADMIN"])


def cmd_get_summary():
    return BotCommand("get_summary", get_summary,
                      help_text="запрос сводки",
                      acceptable_roles=["ADMIN"])


def make_stats_addon():
    return BotAddon("Stats", "статистика",
                    [cmd_get_stats(), cmd_get_summary()])
