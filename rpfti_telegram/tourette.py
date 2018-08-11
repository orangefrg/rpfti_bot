import os
import random
from .core_addon import BotCommand, BotAddon, BotTask

path = os.path.dirname(os.path.abspath(__file__))

words = []

def _loadwords():
    words_loaded = []
    with open(path + "/words/tourette") as w:
        words_loaded = w.readlines()
    return words_loaded


def _get_word():
    return "{}!!!".format(random.choice(words).rstrip())

def subscribe(cmd, db_user, db_chat, message, cmd_args):
    bot = cmd.addon.bot
    task = bot.get_task(db_chat, "Tourette", "random_tourette")
    if task.count() > 0:
        bot.delete_task(db_chat, "Tourette", "random_tourette")
        bot.send_message(db_chat, "Больше не буду присылать случайные матюки",
                         origin_user=db_user, reply_to=message.message_id)
    else:
        if bot.add_task(None, db_chat, "Tourette", "random_tourette", "Случайные матюки", db_user, random_reset=True):
            bot.send_message(db_chat, "Буду присылать случайные матюки теперь",
                            origin_user=db_user, reply_to=message.message_id)
        else:
            bot.send_message(db_chat, "Что-то пошло не так",
                            origin_user=db_user, reply_to=message.message_id)


def tourette_word(task_f, task, task_model):
    bot = task_f.addon.bot
    chat = task.chat
    out_string = _get_word()
    bot.send_message(chat, out_string)
    bot.reset_task(task)
    return True

cmd_subscribe_tourette = BotCommand(
    "tourette", subscribe, help_text="включение режима случайных матюков")
tsk_tourette = BotTask("random_tourette", tourette_word)
tourette_addon = BotAddon("Tourette", "Ругань",
                     [cmd_subscribe_tourette], tasks=[tsk_tourette])

words = _loadwords()