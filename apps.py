from django.apps import AppConfig
import rpfti.shared_config

mainbot = None


def get_bot():
    global mainbot
    return mainbot


class RpftiConfig(AppConfig):
    name = 'rpfti'

    def ready(self):
        from rpfti.rpfti_telegram.core import BotCore
        from rpfti.rpfti_telegram.core_addon import core_addon
        from rpfti.rpfti_telegram.whoami import noporn_addon
        from rpfti.rpfti_telegram.stats import stats_addon
        from rpfti.rpfti_telegram.rss import rss_addon
        from rpfti.models import Bot, TelegramUser, TelegramChat
        from rpfti.models import Message, Like

        global mainbot
        shared_config = rpfti.shared_config
        main_models = {}
        main_models["Bots"] = Bot
        main_models["Chats"] = TelegramChat
        main_models["Users"] = TelegramUser
        main_models["Messages"] = Message
        main_models["Likes"] = Like

        settings = {}
        settings["url"] = shared_config.WEBHOOK_URL_BASE + \
            shared_config.WEBHOOK_URL_PATH
        settings["cert"] = shared_config.WEBHOOK_SSL_CERT
        settings["token"] = shared_config.TOKEN_NOPORN
        settings["name"] = "RemoveThatPicBot"
        settings["description"] = "Porn remover bot"

        roles = {}
        roles["o_range"] = "ADMIN"

        mainbot = BotCore(main_models, settings, roles)
        mainbot.insert_addon(core_addon)
        mainbot.insert_addon(noporn_addon)
        mainbot.insert_addon(stats_addon)
        mainbot.insert_addon(rss_addon)
        mainbot.bind()

        ctrl_settings = {}
        ctrl_settings["url"] = shared_config.WEBHOOK_URL_BASE + \
            shared_config.WEBHOOK_URL_PATH_CONTROL
        ctrl_settings["cert"] = shared_config.WEBHOOK_SSL_CERT
        ctrl_settings["token"] = shared_config.TOKEN_TEST
        ctrl_settings["name"] = "Control_Bot"
        ctrl_settings["description"] = "Control bot"

        # controlbot = BotCore(main_models, ctrl_settings, roles)
        # controlbot.insert_addon(core_addon)
        # controlbot.bind()

        print("READY!")
