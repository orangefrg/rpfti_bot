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


# Packed bot addon with commands and callbacks


class BotAddon:

    def __init__(self, name, description, commands=[],
                 callbacks=[]):
        self.name = name
        self.description = description
        self.commands = commands
        self.callbacks = callbacks
        for c in self.commands:
            c.addon = self
        for c in self.callbacks:
            c.addon = self


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


cmd_start = BotCommand("start", start_bot,
                       help_text="запустить бота для данного чата")
cmd_stop = BotCommand("stop", stop_bot,
                      help_text="отключить бота для данного чата")
cmd_start_global = BotCommand("start_g", start_global,
                              acceptable_roles=["ADMIN"],
                              help_text="включить бота глобально")
cmd_stop_global = BotCommand("stop_g", stop_global,
                             acceptable_roles=["ADMIN"],
                             help_text="отключить бота глобально")
cmd_help = BotCommand("help", get_help,
                      help_text="вывести это сообщение")


core_addon = BotAddon("Main", "основное управление ботом",
                      [cmd_start, cmd_stop,
                       cmd_start_global, cmd_stop_global,
                       cmd_help])
