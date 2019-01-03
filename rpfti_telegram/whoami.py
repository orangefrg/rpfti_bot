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
import json
from telebot import types
from .namez import get_random_name
import datetime
import pymorphy2

valid_acronym_banned = ["Ы", "Ь", "Ъ"]

cached_acronyms = {}
cached_acronyms_adj = {}


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


prepositions = [
    ("от", "gent"),
    ("к", "datv"),
    ("из-за", "gent"),
    ("без", "gent"),
    ("за", "accs"),
    ("до", "gent"),
    ("на", "accs"),
    ("по", "datv"),
    ("о", "loct"),
    ("перед", "ablt"),
    ("при", "loct"),
    ("через", "accs"),
    ("с", "gent"),
    ("у", "gent"),
    ("над", "loct"),
    ("об", "loct"),
    ("под", "ablt"),
    ("про", "accs"),
    ("для", "gent"),
    ("вблизи", "gent"),
    ("вглубь", "gent"),
    ("вдоль", "gent"),
    ("возле", "gent"),
    ("около", "gent"),
    ("вокруг", "gent"),
    ("впереди", "gent"),
    ("наподобие", "gent"),
    ("согласно", "datv")
]

companies = [
    "ООО",
    "АО",
    "ПАО"
]

company_forms = [
    """{adj,noun}""",
    """{noun}""",
    """{noun}{prepos,noun}""",
    """{name}{prepos,noun}""",
    """{adj}{name}""",
    """{name}, {name} и {name}""",
    """{name} и сыновья""",
    """{noun} - {noun_case:datv}"""
]

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
              
whoami_forms = [
    """{adj,noun} {prepos,adj,noun}""",
    """{adj,noun}{connect}{adj,noun}""",
    """{adj,noun}: {noun}, {noun}, {noun}""",
    """{noun}{connect}{noun} {adj_case:gent,noun_case:gent}""",
    """{noun} и {noun}!""",
    """{noun} по имени {name}""",
    """{adj,noun} по имени {name}""",
    """{name}{connect}{adj,noun}!"""
]

MAX_PHRASES = 2
NOPORN_PAIRS = 6
ACRONYM_LENGTH_LIMIT = 25

words_adj = []
big_arr = {}

morph = pymorphy2.MorphAnalyzer()

professions = {}

def loadwords():
    global big_arr
    global words_adj
    global professions
    path = os.path.dirname(os.path.abspath(__file__))
    f_male = open(path + "/words/dict.male")
    f_female = open(path + "/words/dict.female")
    f_indef = open(path + "/words/dict.indef")
    f_adj = open(path + "/words/dict.adj")
    f_prof = open(path + "/words/professions.json")
    words_male = f_male.readlines()
    words_female = f_female.readlines()
    words_indef = f_indef.readlines()
    words_adj = f_adj.readlines()
    professions = json.load(f_prof)
    f_male.close()
    f_female.close()
    f_indef.close()
    f_adj.close()
    f_prof.close()
    big_arr = {'male': words_male,
               'female': words_female, 'indef': words_indef}
    logging.info('''Loaded {} male, {} female,
                   {} indef nouns and {} adjectives'''.format(
                 len(words_male), len(words_female),
                 len(words_indef), len(words_adj)))

def gender_change(word, gender):
    if gender == 'female':
        word = re.sub("(\S+)([с|н])ий$", "\g<1>\g<2>яя", word)
        word = re.sub("(\S+)([и|ы|о]й)$", "\g<1>ая", word)
        word = re.sub("(\S+)([н|в])$", "\g<1>\g<2>а", word)
        word = re.sub("(\S+)([ий|ый|ой]ся)$", "\g<1>аяся", word)
    elif gender == 'indef':
        word = re.sub("(\S+)([с|н])ий$", "\g<1>\g<2>ее", word)
        word = re.sub("(\S+)([и|ы|о]й)$", "\g<1>ое", word)
        word = re.sub("(\S+)([н|в])$", "\g<1>\g<2>о", word)
        word = re.sub("(\S+)([ий|ый|ой]ся)$", "\g<1>ееся", word)
    return word


def get_random_noun():
    key = random.choice(list(big_arr.keys()))
    selected_words = big_arr[key]
    noun = random.choice(selected_words)
    return key, noun.strip()


def get_random_adj(gender):
    adj = gender_change(random.choice(words_adj), gender)
    return adj.strip()

def parse_form(form):
    templ = re.compile("\{([\w,_:]+)\}")
    template = []
    lastpos = 0
    for mtch in templ.finditer(form):
        current_options = []
        for match_part in mtch.group(1).split(","):
            part = {}
            if "_" in match_part:
                match_part_subparts = match_part.split("_")
                part["name"] = match_part_subparts[0]
                for p in match_part_subparts[1:]:
                    part[p.split(":")[0]] = p.split(":")[1]
            else:
                part["name"] = match_part
            current_options.append(part)
        if mtch.start() != lastpos:
            template.append([{
                "name": "spacer",
                "value": form[lastpos:mtch.start()]
            }])
        lastpos = mtch.end()
        template.append(current_options)
    if lastpos < len(form):
        template.append([{
            "name": "spacer",
            "value": form[lastpos:len(form)]
        }])
    return template

def make_string_from_template(template):
    out_string = ""
    for options in template:
        gender = None
        case = None
        for i in range(2):
            for opt in options:
                if opt["name"] == "noun":
                    current_case = None
                    if not "value" in opt:
                        gender, opt["value"] = get_random_noun()
                    if "case" in opt:
                        current_case = opt["case"]
                    elif case is not None:
                        current_case = case
                    if current_case is not None:
                        prs = morph.parse(opt["value"])[0]
                        opt["value"] = prs.inflect({current_case}).word
                elif opt["name"] == "adj":
                    current_case = None
                    if not "value" in opt:
                        opt["value"] = get_random_adj("male")
                    if gender in ["female", "indef"]:
                        opt["value"] = gender_change(opt["value"], gender)
                    if "case" in opt:
                        current_case = opt["case"]
                    elif case is not None:
                        current_case = case
                    if current_case is not None:
                        prs = morph.parse(opt["value"])[0]
                        opt["value"] = prs.inflect({current_case}).word
                elif opt["name"] == "prepos":
                    if not "value" in opt:
                        prep = random.choice(prepositions)
                        opt["value"] = prep[0]
                        case = prep[1]
                elif opt["name"] == "connect":
                    if not "value" in opt:
                        opt["value"] = random.choice(separators)
                elif opt["name"] == "name":
                    opt["value"] = get_random_name()
        options_string = " ".join([a["value"] for a in options])
        out_string += options_string
    return out_string

def make_phrase(username):
    outstr = username + ", ты - "
    templ = parse_form(random.choice(whoami_forms))
    outstr += make_string_from_template(templ)
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
    bot.send_message(chat, txt, origin_user=user,
                    markup=apply_like_markup(),
                    reply_to=message.message_id)


def dreamteam(cmd, user, chat, message, cmd_args):
    out_str = "Твоя команда мечты:\n\n"
    out_str += "Тренер: {}\n".format(get_random_name())
    out_str += "Вратарь: {}\n".format(get_random_name())
    out_str += "Защитники: "
    for i in range(4):
        out_str += "{}, ".format(get_random_name())
    out_str += "\nПолузащитники: "
    for i in range(4):
        out_str += "{}, ".format(get_random_name())
    out_str += "\nНападающие: "
    for i in range(2):
        out_str += "{}, ".format(get_random_name())
    bot = cmd.addon.bot
    bot.send_message(chat, out_str, origin_user=user,
                     markup=apply_like_markup(),
                     reply_to=message.message_id)


def get_random_profession():
    profession = professions[random.choice(professions.keys())]
    templ = parse_form(random.choice(company_forms))
    outstr = "{} в {} \"{}\"".format(profession, random.choice(companies), make_string_from_template(templ))
    return outstr


def my_profession(cmd, user, chat, message, cmd_args):
    out_str = "Твоя психологическая профессия:\n{}".format(get_random_profession)
    bot = cmd.addon.bot
    bot.send_message(chat, out_str, origin_user=user,
                     markup=apply_like_markup(),
                     reply_to=message.message_id)


def acronym_preprocessing(acronym):
    acronym_parts = []
    acronym = re.sub("[^а-яА-Я]", "", acronym)
    all_upper = False
    for a in acronym:
        if all_upper:
            a = a.upper()
        if a.islower():
            if len(acronym_parts) > 0:
                acronym_parts[-1] += a
            elif a.upper() not in valid_acronym_banned:
                acronym_parts.append(a.upper())
                all_upper = True
        elif a not in valid_acronym_banned:
            acronym_parts.append(a)
    return acronym_parts


def get_acronym_definition_noun(acronym_part):
    global big_arr
    global cached_acronyms
    acronym_part = acronym_part.lower()
    matching_words = []
    if acronym_part in cached_acronyms:
        matching_words = cached_acronyms[acronym_part]
    else:
        for gender in big_arr:
            for word in big_arr[gender]:
                if re.match("{}(.+)".format(acronym_part), word):
                    if len(word)==1:
                        print(word)
                        print(word)
                        print(word)
                    matching_words.append((word, gender))
        cached_acronyms[acronym_part] = matching_words
    if len(matching_words) == 0:
        return None
    return matching_words


def get_acronym_definition_adj(acronym_part, gender):
    global big_arr
    global cached_acronyms_adj
    acronym_part = acronym_part.lower()
    matching_words = []
    if acronym_part in cached_acronyms_adj:
        matching_words = cached_acronyms_adj[acronym_part]
    else:
        for word in words_adj:
            if re.match("{}(.+)".format(acronym_part), word):
                matching_words.append(word)
        cached_acronyms_adj[acronym_part] = matching_words
    if len(matching_words) == 0:
        return None
    return [gender_change(w, gender) for w in matching_words]


def get_acronym_as_motto(acronym_parts):
    global big_arr
    definition = []
    for p in acronym_parts:
        matching_words = get_acronym_definition_noun(p)
        part_def = random.choice(matching_words)
        if p is None:
            return None
        definition.append(part_def[0])
    out_str = ""
    if len(definition) > 1:
        out_str += definition[0][0].upper() + definition[0][1:].strip() + ": "
        out_str += ", ".join([w.strip() for w in definition[1:]])
        out_str += "!"
    else:
        out_str = definition[0][0].upper() + definition[0][1:].strip() + "!"
    return out_str


def get_acronym_standard(acronym_parts):
    acronym_scheme = []
    acronym_definition = []
    out_str = ""
    if len(acronym_parts) == 1:
        matching_words = get_acronym_definition_noun(acronym_parts[0])
        if matching_words is None:
            return None
        out_str = random.choice(matching_words)[0]
        return out_str
    acronym_scheme.append((acronym_parts[-1], "noun"))
    for part in reversed(acronym_parts[:-1]):
        if random.randrange(100) >= 50:
            acronym_scheme.append((part, "noun"))
        else:
            acronym_scheme.append((part, "adj"))
    last_gender = ""
    for scheme_part in acronym_scheme:
        if scheme_part[1] == "noun":
            matching_words = get_acronym_definition_noun(scheme_part[0])
            if matching_words is None:
                return None
            selection = random.choice(matching_words)
            if len(acronym_definition) > 0:
                acronym_definition[-1] = acronym_definition[-1][0].upper() + acronym_definition[-1][1:]
            acronym_definition.append(selection[0].strip() + ".")
            last_gender = selection[1]
        elif scheme_part[1] == "adj":
            matching_words = get_acronym_definition_adj(scheme_part[0], last_gender)
            acronym_definition.append(random.choice(matching_words).strip())
    out_str = " ".join(reversed(acronym_definition))
    out_str = out_str[0].upper() + out_str[1:]
    return out_str


def translate_acronym_worker(acronym):
    acronym_parts = acronym_preprocessing(acronym)
    out_str = ""
    if random.randrange(100) >= 50:
        out_str = get_acronym_as_motto(acronym_parts)
    else:
        out_str = get_acronym_standard(acronym_parts)
    if out_str is None:
        return "Не удалось расшифровать аббревиатуру. Что-то пошло не так."
    acronym_with_dots = ". ".join(acronym_parts) + "."
    out_str = "{} означает:\n\n{}".format(acronym_with_dots, out_str)
    return out_str


def translate_acronym(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    txt = ""
    markup = None
    if len(cmd_args) == 0:
        txt = "Пришли аббревиатуру ответом на это сообщение"
        all_sent = bot.send_message(chat, txt, origin_user=user,
                        reply_to=message.message_id)
        context = {
            "command": "acronym",
            "action": "request_reply"
        }
        for a in all_sent:
            bot.keep_context(cmd.addon, context, a.message_id)
    elif len(cmd_args) > ACRONYM_LENGTH_LIMIT:
        txt = "Слишком длинно. Больше {} символов пока нельзя".format(ACRONYM_LENGTH_LIMIT)
        bot.send_message(chat, txt, origin_user=user,
                        reply_to=message.message_id)
    else:
        txt, outcome = translate_acronym_worker(cmd_args)
        if outcome:
            markup = apply_like_markup()
        bot.send_message(chat, txt, origin_user=user,
                        markup=markup,
                        reply_to=message.message_id)


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
        out_str = "Удалены все {} сообщений".format(cnt)
    else:
        out_str = "Нечего удалять, эй"
    bot.send_message(chat, origin_user=user, text=out_str,
                     reply_to=message.message_id)


def delete_liked(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    mdl = bot.models["Likes"]
    liked = mdl.objects.filter(liked_by=user)
    number_match = re.search("(\d+)", cmd_args)
    if len(liked) > 0:
        if not number_match:
            out_str = "Не понимаю, какое удалять. Нужно указать номер в явном виде." \
                      "Например, \"/delete_liked 4\""
        else:
            number = int(number_match.group(1))
            if number in range(1, len(liked)):
                liked[number - 1].delete()
                out_str = "Удалено сообщение номер {}".format(number)
            else:
                out_str = "Не получится удалить - понравилось всего {} сообщений".format(len(liked))

    else:
        out_str = "Нечего удалять, эй"
    bot.send_message(chat, origin_user=user, text=out_str,
                     reply_to=message.message_id)


def whoami_reply_handler(addon, db_context, context, user, chat, message):
    bot = addon.bot
    markup = None
    if "command" in context:
        if context["command"] == "acronym":
            if "action" in context and context["action"] == "request_reply":
                if message.text is None:
                    if message.photo is not None:
                        txt = "Ты мне ещё ньюдс пришли..."
                    else:
                        txt = "Нужно прислать текст"
                elif len(message.text) == 0:
                    txt = "Текст что-то пустой"
                elif len(message.text) > ACRONYM_LENGTH_LIMIT:
                    txt = "Длинновато, пока что нужно менее {} символов".format(ACRONYM_LENGTH_LIMIT)
                else:
                    txt = translate_acronym_worker(message.text)
                    markup = apply_like_markup()
                bot.send_message(chat, txt, origin_user=user,
                                markup=markup,
                                reply_to=message.message_id)
                


loadwords()

cmd_noporn = BotCommand(
    "x", antiporn, help_text="скрыть плохую картинку стикерами и сообщениями")
cmd_whoami = BotCommand(
    "whoami", whoami, help_text="познать себя")
cmd_my_profession = BotCommand(
    "myprof", my_profession, help_text="моя психологическая профессия"
)
cmd_dreamteam = BotCommand(
    "dreamteam", dreamteam, help_text="составить свою команду мечты")
cmd_get_liked = BotCommand(
    "get_liked", get_liked, help_text="получить список понравившегося")
cmd_delete_liked = BotCommand(
    "delete_liked", delete_liked, help_text="удалить определённое понравившееся сообщение")
cmd_clear_liked = BotCommand(
    "clear_liked", clear_liked, help_text="очистить список понравившегося")
cmd_acronym = BotCommand(
    "acr", translate_acronym, help_text="расшифровать аббревиатуру")

cb_like = BotCallback("set_like", like_callback)

noporn_addon = BotAddon("NoPorn", "познание себя через отказ от порно",
                        [cmd_noporn, cmd_whoami, cmd_my_profession, cmd_dreamteam, cmd_acronym,
                         cmd_get_liked, cmd_delete_liked,
                         cmd_clear_liked], [cb_like], reply_handler=whoami_reply_handler)
