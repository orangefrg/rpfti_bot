from .core_addon import BotCommand, BotAddon


def get_statistics(cmd, user, chat, message, cmd_args):
    text = "Запрос полной статистики..."
    cmd.addon.bot.send_message(chat, origin_user=user, text=text,
                               reply_to=message.message_id)
    bot = cmd.addon.bot
    bots = bot.models["Bots"]
    chats = bot.models["Chats"]
    users = bot.models["Users"]
    messages = bot.models["Messages"]
    # likes = bot.models["Likes"]
    out_string = "Полная статистика\n"

    for b in bots.objects.all():
        out_string += "Бот {} (запущен {})\n\n".format(b.name, b.start_time)
        for c in chats.objects.filter(bot=b):
            if c.chat_type in ["group", "supergroup"]:
                out_string += "Чат {}".format(c.title)
            elif c.chat_type == "channel":
                out_string += "Канал {}".format(c.title)
            elif c.chat_type == "private":
                out_string += "Личные сообщения с {} {} {}".format(
                    c.first_name, c.user_name, c.last_name)
            else:
                out_string += "Неизвестный тип диалога: {}".format(
                    c.telegram_id)
            out_string += " (добавлен {})".format(c.init_date)
            if c.is_active:
                out_string += " и сейчас активен\n\n"
            else:
                out_string += " и сейчас отключен\n\n"
            out_string += "Всего {} сообщений\n".format(
                messages.objects.filter(chat=c).count())
        out_string += "\n\nПользователи:\n"
        for u in users.objects.filter(bot=b):
            out_string += "{} {} {} - {}\n".format(
                u.first_name, u.user_name, u.last_name,
                messages.objects.filter(to_user=u).count())
    cmd.addon.bot.send_message(chat, origin_user=user, text=out_string,
                               reply_to=message.message_id)


cmd_get_stats = BotCommand(
    "get_stats", get_statistics, help_text="запрос статистики",
    acceptable_roles=["ADMIN"])
stats_addon = BotAddon("Stats", "статистика",
                        [cmd_get_stats])
