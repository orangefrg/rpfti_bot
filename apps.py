from django.apps import AppConfig
import rpfti.shared_config
whoamibot = None
infobot = None
amoralbot = None
initial_signal = 99
# Check if bot is launched under uwsgi
has_uwsgi = False
try:
    import uwsgi
    has_uwsgi = True
except:
    print("WARNING! No UWSGI found")

def get_whoami():
    global whoamibot
    return whoamibot

def get_infobot():
    global infobot
    return infobot

def get_amoralbot():
    global amoralbot
    return amoralbot

class RpftiConfig(AppConfig):
    name = 'rpfti'

    def prepare_bot(self, bot_core, models, settings, roles, addons):
        global initial_signal
        bot = bot_core(models, settings, roles)
        for a in addons:
            bot.insert_addon(a)
        bot.bind()
        
        def check_tasks(signum):
            bot.check_tasks()

        uwsgi.register_signal(initial_signal, "", check_tasks)
        uwsgi.add_timer(initial_signal, 10)
        initial_signal -= 1

        for k, v in roles.items():
            if v == "ADMIN":
                if has_uwsgi:
                    try:
                        db_chat = bot.models["Chats"].objects.get(
                            bot__name=bot.name, user_name=k)
                        bot.send_message(db_chat, "Бот перезапущен")
                    except:
                        print("No admin found")

        return bot



    def ready(self):
        from rpfti.rpfti_telegram.core import BotCore
        from rpfti.rpfti_telegram.core_addon import make_core_addon
        from rpfti.rpfti_telegram.whoami import make_noporn_addon
        from rpfti.rpfti_telegram.stats import make_stats_addon
        from rpfti.rpfti_telegram.rss import make_rss_info_addon, make_rss_nudes_addon
        from rpfti.rpfti_telegram.tourette import make_tourette_addon
        from rpfti.rpfti_telegram.datacon_weather import make_weather_addon
        from rpfti.rpfti_telegram.cbrf import make_cbrf_addon
        from rpfti.models import Bot, TelegramUser, TelegramChat
        from rpfti.models import Message, Like, ScheduledTask, TouretteUser
        from rpfti.models import Context

        if not has_uwsgi:
            print("Dummy run (without UWSGI)")
            return True

        shared_config = rpfti.shared_config
        models = {
            "Bots": Bot,
            "Chats": TelegramChat,
            "Users": TelegramUser,
            "Messages": Message,
            "Likes": Like,
            "Tasks": ScheduledTask,
            "TouretteUser": TouretteUser,
            "Context": Context
        }

        wai_settings = {
            "url": shared_config.WEBHOOK_URL_BASE + shared_config.WEBHOOK_URL_PATH_WAI,
            "cert": shared_config.WEBHOOK_SSL_CERT,
            "token": shared_config.TOKEN_WAI,
            "name": "WhoAmIBot",
            "description": "Self-science bot"
        }

        infobot_settings = {
            "url": shared_config.WEBHOOK_URL_BASE + shared_config.WEBHOOK_URL_PATH_INFO,
            "cert": shared_config.WEBHOOK_SSL_CERT,
            "token": shared_config.TOKEN_INFO,
            "name": "RPFInfoBot",
            "description": "Simple information bot"
        }

        amoral_settings = {
            "url": shared_config.WEBHOOK_URL_BASE + shared_config.WEBHOOK_URL_PATH_AMORAL,
            "cert": shared_config.WEBHOOK_SSL_CERT,
            "token": shared_config.TOKEN_AMORAL,
            "name": "VeryAmoralBot",
            "description": "Amoral bot"
        }

        roles = {}
        roles["o_range"] = "ADMIN"

        wai_addons = [make_core_addon(), make_noporn_addon(), make_stats_addon()]
        info_addons = [make_core_addon(), make_stats_addon(), make_rss_info_addon(), make_cbrf_addon()]
        amoral_addons = [make_core_addon(), make_stats_addon(), make_rss_nudes_addon(), make_tourette_addon()]
        global whoamibot
        global infobot
        global amoralbot
        whoamibot = self.prepare_bot(BotCore, models, wai_settings, roles, wai_addons)
        infobot = self.prepare_bot(BotCore, models, infobot_settings, roles, info_addons)
        amoralbot = self.prepare_bot(BotCore, models, amoral_settings, roles, amoral_addons)
        print(whoamibot.name)
        print(infobot.name)
        print(amoralbot.name)

        print("READY!")
