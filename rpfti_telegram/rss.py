import feedparser
import requests
import json
import rpfti.shared_config
import random
from .core_addon import BotCommand, BotAddon

rss_art = "http://backend.deviantart.com/rss.xml?q=boost%3Apopular+"\
          "max_age%3A24h+in%3Aphotography&amp;type=deviation"

api_url = "https://www.googleapis.com/urlshortener/v1/url?key={}".format(
    rpfti.shared_config.GOO_GL)
headers = {'content-type': 'application/json'}

rss_list = ["https://news.yandex.ru/Tajikistan/index.rss",
            "http://breakingmad.me/ru/rss",
            "http://batenka.ru/rss/",
            "http://orthodoxy.cafe/index.php?PHPSESSID=ssfp967ein7mpt6dklev0ko1b6&action=.xml;board=65;type=rss",
            "http://orthodoxy.cafe/index.php?PHPSESSID=ssfp967ein7mpt6dklev0ko1b6&action=.xml;board=66;type=rss",
            "http://ren.tv/export/feed.xml",
            ]

drama_list = ["https://www.galya.ru/sitemap/rss20export.xml",
              "http://www.woman.ru/forum/rss/"]


def make_short(url):
    payload = {'longUrl': url}
    r = requests.post(api_url, data=json.dumps(payload), headers=headers)
    return r.json()["id"]


def get_drama(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    try:
        out_msg = "Немного важных драм, {}\n".format(user.first_name)
        r = feedparser.parse(random.choice(drama_list))
        n = random.choice(r["entries"])
        out_msg += "Вот, например, \"{}\" из категории \"{}\"\n\n{}\n\n{}".format(
            n["title"], n["category"], n["description"], n["guid"])
        bot.send_message(chat, out_msg, origin_user=user, disable_preview=True)
    except Exception as e:
        print(e)
        bot.send_message(
            chat, "Не удалось что-то с драмами...", origin_user=user)


def get_news(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    try:
        out_msg = "Вот тебе новостей, {}\n".format(user.first_name)
        for i in range(3):
            r = feedparser.parse(random.choice(rss_list))
            n = random.choice(r["entries"])
            print(n)
            slink = make_short(n["link"])
            title = n["title"]
            feed_title = r["feed"]["title"]
            if "published" in n:
                pubdate = n["published"]
            elif "pubDate" in n:
                pubdate = n["pubDate"]
            elif "updated" in n:
                pubdate = n["updated"]
            else:
                pubdate = "хер его знает, когда"
            out_msg += "---\n{}\n{}\n({}, опубликовано: {})\n".format(
                title, slink, feed_title, pubdate)
        bot.send_message(chat, out_msg, origin_user=user, disable_preview=True)
    except Exception as e:
        print(e)
        bot.send_message(
            chat, "Не удалось что-то с новостями...", origin_user=user)


def get_art(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    try:
        rss_art = "http://backend.deviantart.com/rss.xml?"\
            "q=boost%3Apopular+max_age%3A24h+in%3A"\
            "photography&amp;type=deviation"
        r = feedparser.parse(rss_art)
        payload = {}
        payload["PHOTO"] = {}
        if len(r["entries"]) == 0:
                bot.send_message(chat, "Картинок не нашлось", origin_user=user)
                return
        ent = random.choice(r["entries"])
        pht = ent["media_content"][0]["url"]
        payload["PHOTO"]["title"] = ent["title"]
        payload["PHOTO"]["file"] = pht
        slink = make_short(pht)
        bot.send_message(chat, slink, origin_user=user, payload=payload,
                         disable_preview=True)
    except Exception as e:
        bot.send_message(
            chat, "Не удалось что-то с картинками...", origin_user=user)
        print(e)


cmd_drama = BotCommand(
    "drama", get_drama, help_text="случайная драма с сайтов с драмами")
cmd_news = BotCommand(
    "news", get_news, help_text="три случайных новости")
cmd_art = BotCommand(
    "art", get_art, help_text="картинка с DeviantArt")
rss_addon = BotAddon("RSS", "работа с RSS",
                     [cmd_news, cmd_art, cmd_drama])
