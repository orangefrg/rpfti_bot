from datetime import timedelta, datetime
import json


class BotCommand:

    def __init__(self, command_text, command_function,
                 acceptable_roles=["ADMIN", "EDIT", "MOD", "USER"],
                 help_text=None):
        self.name = command_text
        self.func = command_function
        self.roles = acceptable_roles
        self.help = help_text

    def call(self, db_user, db_chat, message, cmd_args=None):
        if db_user.role not in self.roles:
            return
        self.func(self, db_user, db_chat, message, cmd_args)


# Bot callback class
# Used to process callbacks (e.g. 'buttons' under bot messages)
class BotCallback:

    def __init__(self, cb, callback):
        self.cb = cb
        self.callback = callback

    # Function calling
    def call(self, db_user, db_chat, cb):
        self.callback(self, db_user, db_chat, cb)


# Bot periodic/scheduled task class
class BotTask:

    def __init__(self, name, task_function):
        self.name = name
        self.task_function = task_function

    def call(self, task, task_model):
        return self.task_function(self, task, task_model)


# Packed bot addon with commands and callbacks
class BotAddon:

    def __init__(self, name, description, commands=[],
                 callbacks=[], tasks=[], reply_handler=None):
        self.name = name
        self.description = description
        self.commands = commands
        self.callbacks = callbacks
        self.tasks = tasks
        self.reply_handler = reply_handler
        for c in self.commands:
            c.addon = self
        for c in self.callbacks:
            c.addon = self
        for t in self.tasks:
            t.addon = self

    def process_reply(self, db_context, user, chat, message):
        if self.reply_handler is not None:
            context = json.loads(db_context.context)
            return self.reply_handler(self, db_context,
                                      context, user, chat,
                                      message)
        return False


def start_bot(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    models = bot.models
    if models["Bots"].objects.get(name=bot.name).is_active:
        if not chat.is_active:
            chat.is_active = True
            chat.save()
            text = "Бот включен для данного чата, {}".format(user.first_name)
        else:
            text = "Бот УЖЕ включен для данного чата, {}".format(
                user.first_name)
        bot.send_message(chat, text, force=True, origin_user=user)


def stop_bot(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    models = bot.models
    if models["Bots"].objects.get(name=bot.name).is_active:
        if chat.is_active:
            chat.is_active = False
            chat.save()
            text = "Бот отключен, {}".format(user.first_name)
            bot.send_message(chat, text, force=True, origin_user=user)


def start_global(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    print("START GLOBAL FROM {}".format(bot.name))
    models = bot.models
    db_bot = models["Bots"].objects.get(name=bot.name)
    if db_bot.is_active:
        text = "Бот уже включен глобально!"
    else:
        text = "Бот включен глобально"
        db_bot.is_active = True
        db_bot.save()
    bot.send_message(chat, text, force=True, origin_user=user)


def stop_global(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    models = bot.models
    db_bot = models["Bots"].objects.get(name=bot.name)
    if db_bot.is_active:
        text = "Бот отключен глобально"
        db_bot.is_active = False
        db_bot.save()
        bot.send_message(chat, text, force=True, origin_user=user)


def get_help(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    text = "Доступные команды:"
    for a in bot.addons:
        addon_text = "\n" + a.name + ":\n"
        command_text = ""
        for c in a.commands:
            if user.role in c.roles:
                command_text += "/{} - {}\n".format(c.name, c.help)
        if len(command_text) > 0:
            text += addon_text + command_text
        text += "\n"
    bot.send_message(chat, text, force=True, origin_user=user,
                     reply_to=message.message_id)


def heartbeat_task(task_f, task, task_model):
    bot = task_f.addon.bot
    chat = task.chat
    bot.send_message(chat, "Ping")
    bot.reset_task(task, delta=timedelta(minutes=1))
    return True


def enable_heartbeat(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    if bot.add_task(datetime.utcnow(), chat, "Main", "heartbeat",
                    "Test heartbeat task - \"Ping\" message every minute",
                    user):
        bot.send_message(chat, "Enabled", origin_user=user,
                         reply_to=message.message_id)
    else:
        bot.send_message(chat, "Already enabled", origin_user=user,
                         reply_to=message.message_id)


def disable_heartbeat(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    bot.delete_task(chat, "Main", "heartbeat")
    bot.send_message(chat, "Disabled", origin_user=user,
                     reply_to=message.message_id)


def disable_tasks(cmd, user, chat, message, cmd_args):
    bot = cmd.addon.bot
    bot.delete_task(chat)
    bot.send_message(chat, "Удалены все задачи", origin_user=user,
                     reply_to=message.message_id)


def cmd_start():
    return BotCommand("start", start_bot,
                      help_text="запустить бота для данного чата")


def cmd_stop():
    return BotCommand("stop", stop_bot,
                      help_text="отключить бота для данного чата")


def cmd_start_global():
    return BotCommand("start_g", start_global,
                      acceptable_roles=["ADMIN"],
                      help_text="включить бота глобально")


def cmd_stop_global():
    return BotCommand("stop_g", stop_global,
                      acceptable_roles=["ADMIN"],
                      help_text="отключить бота глобально")


def cmd_help():
    return BotCommand("help", get_help,
                      help_text="вывести это сообщение")


def cmd_start_hb():
    return BotCommand("start_hb", enable_heartbeat,
                      acceptable_roles=["ADMIN"],
                      help_text="enable heartbeat")


def cmd_stop_hb():
    return BotCommand("stop_hb", disable_heartbeat,
                      acceptable_roles=["ADMIN"],
                      help_text="disable heartbeat")


def cmd_clear_tasks():
    return BotCommand("clear_tasks", disable_tasks,
                      acceptable_roles=["ADMIN"],
                      help_text="очистить планировщик для данного чата")


def tsk_heartbeat():
    return BotTask("heartbeat", heartbeat_task)


def make_core_addon():
    return BotAddon("Main", "основное управление ботом",
                    [cmd_start(), cmd_stop(),
                     cmd_start_global(), cmd_stop_global(),
                     cmd_help(), cmd_start_hb(), cmd_stop_hb(),
                     cmd_clear_tasks()], tasks=[tsk_heartbeat()])

