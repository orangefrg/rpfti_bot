# Porn hunter and wisdom bringer
# Can throw several ramdom words and stickers in order to "scroll" chat window
# Also, can send two random phrases (adjective + noun)
# in correct grammatic form
# Currently, only russian language is supported

from .core_addon import BotCommand, BotAddon, BotCallback
import logging
import time
import os
import re
import random
from telebot import types
import datetime

stckr_np = ["BQADAgADAQIAApkvSwqccXZn3KlM4gI",
            "BQADAgADHwADpnZvDBxwFN2m2olrAg",
            "BQADAgADFwAD--ADAAHJXmemCcVOrAI",
            "BQADAgADgAAD--ADAAFvdYyygXgzOgI",
            "BQADAgADfgAD--ADAAHIl2oBIzb2hwI",
            "BQADBAADbAADXSupASiubI4Zpl2-Ag",
            "BQADAgADCgIAAmkSAAKTrYj84n3CkQI",
            "BQADBQAEAQAC6QrIA71EesQH0JyWAg",
            "BQADAgADdAADvStuBI8qFKVtF31NAg",
            "BQADAgADDgMAApkvSwqnjFNpPz0IPgI",
            "BQADAgADCgkAAjeEMAABvl9EwUg4W3IC",
            "BQADAgADKwUAAgw7AAEKkZrJMEXNKe0C",
            "BQADAgADwgADhGUHCr3KIoB4FwABYQI",
            "BQADAgADiwADn8EEAAG3bORmEDomZQI",
            "BQADBAADYgADudGqAR2YUXZ_mzCqAg",
            "BQADAgADJgIAAqtWmgz1KF6Copj_QwI",
            "BQADBQADBgEAAukKyAN_KpeTpTLWTAI",
            "BQADBAADDBQAAnrRWwYbowLeZzqTpgI",
            "BQADAgADDgMAAqtWmgwqKkx7Jglp8wI",
            "BQADAgAD7AIAAqtWmgwNSBtJt2fqOgI"]

separators = [" и ",
              ". Мы ещё называем это ",
              ", к тому же ещё и ",
              ", не учитывая то, что ты ",
              ". Ты - ",
              ", но для друзей ты просто ",
              ", при этом в прошлой жизни ты явно ",
              ". Не стоит удивляться, ведь ты ещё и ",
              "? Нет, брось, ты - ",
              ", что следует из того, что ты ",
              ", а вчера с утра ты скорее ",
              ". Это нормально для того, чьё имя - ",
              ", ахаха, это как ", ", но мы все зовём тебя "]

MAX_PHRASES = 2
NOPORN_PAIRS = 6

words_adj = []

big_arr = {}


def loadwords():
    global big_arr
    global words_adj
    path = os.path.dirname(os.path.abspath(__file__))
    f_male = open(path + "/words/dict.male")
    f_female = open(path + "/words/dict.female")
    f_indef = open(path + "/words/dict.indef")
    f_adj = open(path + "/words/dict.adj")
    words_male = f_male.readlines()
    words_female = f_female.readlines()
    words_indef = f_indef.readlines()
    words_adj = f_adj.readlines()
    big_arr = {'male': words_male,
               'female': words_female, 'indef': words_indef}
    logging.info('''Loaded {} male, {} female,
                   {} indef nouns and {} adjectives'''.format(
                 len(words_male), len(words_female),
                 len(words_indef), len(words_adj)))


def make_phrase(username):
    outstr = username + ", ты - "
    definitions = []
    for i in range(MAX_PHRASES):
        key = random.choice(list(big_arr.keys()))
        selected_words = big_arr[key]
        noun = random.choice(selected_words)
        adj = random.choice(words_adj)
        if key == 'female':
            adj = re.sub("(\S+)([с|н])ий$", "\g<1>\g<2>яя", adj)
            adj = re.sub("(\S+)([и|ы|о]й)$", "\g<1>ая", adj)
            adj = re.sub("(\S+)([н|в])$", "\g<1>\g<2>а", adj)
            adj = re.sub("(\S+)([ий|ый|ой]ся)$", "\g<1>аяся", adj)
        elif key == 'indef':
            adj = re.sub("(\S+)([с|н])ий$", "\g<1>\g<2>ее", adj)
            adj = re.sub("(\S+)([и|ы|о]й)$", "\g<1>ое", adj)
            adj = re.sub("(\S+)([н|в])$", "\g<1>\g<2>о", adj)
            adj = re.sub("(\S+)([ий|ый|ой]ся)$", "\g<1>ееся", adj)
        definitions.append(re.sub("\n", "", adj + " " + noun))
    for i in range(len(definitions)):
        if i < len(definitions) - 1:
            definitions[i] += random.choice(separators)
        outstr += definitions[i]
    return outstr


def like_message(user, bot, message):
    mdl = bot.models["Likes"]
    try:
        try:
            like = mdl.objects.get(bot__name=bot.name,
                                   message__message_id=message.message_id,
                                   message__chat__telegram_id=message.chat.id,
                                   liked_by=user)
            like.delete()
            return "Unlike"
        except mdl.DoesNotExist:
            like = mdl()
            like.bot = bot.models["Bots"].objects.get(name=bot.name)
            like.message = bot.models["Messages"].objects.get(
                message_id=message.message_id,
                bot__name=bot.name,
                chat__telegram_id=message.chat.id)
            like.liked_by = user
            like.date = datetime.datetime.utcnow()
            like.save()
            return "Like"
    except Exception as e:
        print(e)
        return "Error"


def antiporn(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    for i in range(NOPORN_PAIRS):
        payload = {}
        payload["STICKER"] = {}
        payload["STICKER"]["id"] = random.choice(stckr_np)
        text = random.choice(
            big_arr[random.choice(list(big_arr.keys()))])
        bot.send_message(chat, origin_user=user, text=text,
                         mute=True, payload=payload)
        time.sleep(0.3)


def apply_like_markup(likes=0):
    keyboard = types.InlineKeyboardMarkup()
    text = "Нравится!" if likes == 0 else "Нравится! Отметок - {}".format(likes)
    callback_button = types.InlineKeyboardButton(
        text=text, callback_data="set_like")
    keyboard.add(callback_button)
    return keyboard


def whoami(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    txt = make_phrase(user.first_name)
    bot.send_message(chat, txt, origin_user=user, markup=apply_like_markup())


# Bot like callback
def like_callback(cmd, user, chat, cb):
    result = like_message(user, cmd.addon.bot, cb.message)
    if result == "Like":
        text = "{}, сообщение отмечено как "\
            "понравившееся".format(user.first_name)
    elif result == "Unlike":
        text = "{}, отметка о том, что сообщение нравится, "\
            "снята".format(user.first_name)
    else:
        text = "{}, не удалось отметить сообщение, как понравившееся."\
            " Возможно, оно было отправлено "\
            "слишком давно".format(user.first_name)
    total_likes = cmd.addon.bot.models["Likes"].objects.filter(
        bot__name=cmd.addon.bot.name,
        message__message_id=cb.message.message_id,
        message__chat=chat).count()
    cmd.addon.bot.bot.answer_callback_query(cb.id, text)
    cmd.addon.bot.bot.edit_message_reply_markup(
        chat.telegram_id, cb.message.message_id,
        reply_markup=apply_like_markup(total_likes))


def get_liked(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    mdl = bot.models["Likes"]

    liked = mdl.objects.filter(liked_by=user)
    if len(liked) > 0:
        out_str = "Вот, что тебе понравилось, {}:\n".format(user.first_name)
        n = 1
        for l in liked:
            out_str += "{}. {}\n".format(n, l.message.text)
            n += 1
    else:
        out_str = "Нет понравившихся сообщений :("
    bot.send_message(chat, origin_user=user, text=out_str,
                     reply_to=message.message_id)


def clear_liked(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    mdl = bot.models["Likes"]
    liked = mdl.objects.filter(liked_by=user)
    if len(liked) > 0:
        cnt = liked.delete()[0]
        out_str = "Удалено {} сообщений".format(cnt)
    else:
        out_str = "Нечего удалять, эй"
    bot.send_message(chat, origin_user=user, text=out_str,
                     reply_to=message.message_id)


loadwords()

cmd_noporn = BotCommand(
    "x", antiporn, help_text="скрыть плохую картинку стикерами и сообщениями")
cmd_whoami = BotCommand(
    "whoami", whoami, help_text="познать себя")
cmd_get_liked = BotCommand(
    "get_liked", get_liked, help_text="получить список понравившегося")
cmd_clear_liked = BotCommand(
    "clear_liked", clear_liked, help_text="очистить список понравившегося")

cb_like = BotCallback("set_like", like_callback)

noporn_addon = BotAddon("NoPorn", "нет порно!",
                        [cmd_noporn, cmd_whoami, cmd_clear_liked,
                         cmd_get_liked], [cb_like])
