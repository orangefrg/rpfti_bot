
# TODO:
# Repeated CB check
# Control UI
# Sysmon
# Art
# Chat statistics

import datetime
import logging
import telebot
import json
import random
from telebot.apihelper import get_me
from django.db.models import Q

# Bot command class
# Contains command text (as typed by user, but without slashes),
# callback function to process request, help text (description)
# and acceptable roles: basically, these are the following:
# ADMIN as a top role
# EDIT as an editor (content-creator)
# MOD as moderator (rules enforcer)
# USER as a simple default user
# BAN as a blocked user
# Latter can be used to prohibit bot using for certain users
# Acceptable roles should be explicitly set
# By default, command is accessible by anyone, excluding banned ones

# How many times to try ot send a message
GLOBAL_MSG_TRY_LIMIT = 5


class BotCore:

    all_bots = []

    def get_activity(self, chat_id):
        chat = self.models["Chats"].objects.filter(bot__name=self.name,
                                                   telegram_id=chat_id)[0]
        return chat.is_active

    def set_activity(self, chat_id, activity):
        chat = self.models["Chats"].objects.filter(bot__name=self.name,
                                                   telegram_id=chat_id)[0]
        chat.is_active = activity
        chat.save()

    def get_command(self, cmd_name):
        for a in self.addons:
            for c in a.commands:
                if c.name == cmd_name:
                    return (c, a)
        return None

    def insert_addon(self, addon):
        new_cmd_list = []
        for c in addon.commands:
            if self.get_command(c.name) is not None:
                logging.warning("{} is already in command list")
            else:
                new_cmd_list.append(c)
                self.commands_cache.append(c.name)
        addon.commands = new_cmd_list
        self.addons.append(addon)
        addon.bot = self

    def bind(self):
        self.bot.remove_webhook()
        self.bot.set_webhook(url=self.WEBHOOK_URL_BASE,
                             certificate=open(self.WEBHOOK_SSL_CERT,
                                              'r'))
        self.start_time = datetime.datetime.now()
        logging.info("Bot {} binded to webhook".format(self.name))

    def get_activity_global(self):
        bot_db = self.db_bot
        return bot_db.is_active

    def set_activity_global(self, activity):
        bot_db = self.db_bot
        bot_db.is_active = activity
        bot_db.save()

    def __init__(self, models, settings, preset_roles):
        self.declared = False
        self.preset_roles = preset_roles
        self.commands_cache = []
        self.addons = []
        self.models = models
        self.WEBHOOK_URL_BASE = settings["url"]
        self.WEBHOOK_SSL_CERT = settings["cert"]
        self.TOKEN = settings["token"]
        self.bot = telebot.TeleBot(self.TOKEN, threaded=False)
        self.name = settings["name"]
        self.bot.parent_entity_name = self.name
        try:
            db_bot = models["Bots"].objects.get(name__exact=self.name)
        except models["Bots"].DoesNotExist:
            db_bot = models["Bots"](name=self.name)
            db_bot.is_active = False
            db_bot.description = settings["description"]
            db_bot.start_time = datetime.datetime.utcnow()
        myself = get_me(self.TOKEN)
        db_bot.telegram_id = myself["id"]
        db_bot.telegram_name = myself["username"]
        db_bot.save()
        self.db_bot = db_bot
        self.declare()
        self.all_bots.append(self)

    def _log_message(self, message, origin_user):
        new_msg = self.models["Messages"]()
        new_msg.bot = self.models["Bots"].objects.filter(name=self.name)[0]
        new_msg.chat = self.models["Chats"].objects.filter(
            bot__name=self.name,
            telegram_id=message.chat.id)[0]
        new_msg.to_user = origin_user
        new_msg.date = datetime.datetime.fromtimestamp(message.date)
        new_msg.text = message.text
        new_msg.message_id = message.message_id
        if message.sticker is not None:
            new_msg.content = "STICKER"
            new_msg.content_id = message.sticker.file_id
        elif message.audio is not None:
            new_msg.content = "AUDIO"
            new_msg.content_id = message.audio.file_id
        elif message.voice is not None:
            new_msg.content = "VOICE"
            new_msg.content_id = message.voice.file_id
        elif message.photo is not None:
            new_msg.content = "PHOTO"
            photos = []
            for p in message.photo:
                photos.append(p.file_id)
            new_msg.content_id = ",".join(photos)
        elif message.location is not None:
            new_msg.content = "LOCATION"
            new_msg.content_id = str(
                message.location.latitude) + "/" + str(
                message.location.longitude)
        elif message.document is not None:
            new_msg.content = "DOCUMENT"
            new_msg.content_id = message.document.file_id
        elif message.video is not None:
            new_msg.content = "VIDEO"
            new_msg.content_id = message.video.file_id
        elif message.contact is not None:
            new_msg.content = "CONTACT"
            new_msg.content_id = "{} {} - {}, id: {}".format(
                message.contact.first_name, message.contact.last_name,
                message.contact.phone_number, message.contact.user_id)
        else:
            new_msg.content = "PLAIN"
        new_msg.save()

    def trim_message(self, text, limit=4096):
        # Cut text for service insertions
        limit -= 200
        messages = []
        while len(text) > 0:
            if len(text) > limit:
                split_mark = limit
                for c in range(limit):
                    current_position = limit - c
                    if text[current_position] in [" ", "\n"]:
                        split_mark = current_position
                        break
            else:
                split_mark = len(text)
            messages.append(text[:split_mark])
            text = text[split_mark + 1:]
        message_count = len(messages)
        if message_count > 1:
            counter = 1
            for m in messages:
                m += "\n(часть сообщения {}/{})".format(counter, message_count)
                counter += 1
        return messages

    def keep_context(self, addon, context, msg_id=None, user=None, chat=None):
        context_serialized = json.dumps(context)
        stored_context = self.models["Context"](
            bot=self.db_bot,
            addon=addon.name,
            context=context_serialized
        )
        if msg_id is not None:
            stored_context.message = msg_id
        else:
            if user is not None:
                stored_context.user = user
            if chat is not None:
                stored_context.chat = chat
        stored_context.save()

    def _retrieve_context(self, addon, msg_id=None, user=None, chat=None):
        params = {
            "addon": addon.name,
            "bot": self.db_bot,
        }
        if msg_id is not None:
            params["message"] = msg_id
        else:
            if user is not None:
                params["user"] = user
            if chat is not None:
                params["chat"] = chat
        return self.models["Context"].objects.filter(**params)
    
    def modify_context(self, addon, context, msg_id=None,
                       user=None, chat=None):
        # TODO: context modification
        pass

    def get_context(self, addon, msg_id=None, user=None, chat=None):
        context = self._retrieve_context(addon.name, msg_id, user, chat)
        if context is not None and context.count() > 0:
            for c in context:
                c["context"] = json.loads(c["context"])
        return context

    def _get_addons_by_context(self, message, user, chat):
        context = self.models["Context"].\
            objects.filter(message=message.message_id)
        if context.count() == 0:
            context = self.models["Context"].\
                objects.filter(message__isnull=True, user=user, chat=chat)
            if context.count() == 0:
                context = self.models["Context"].objects.filter(
                    Q(message__isnull=True),
                    Q(user=user) & Q(chat__isnull=True) |
                    Q(chat=chat) & Q(user__isnull=True))
        if context.count() == 0:
            return []
        all_addons = {}
        for c in context:
            addons = list(filter(lambda a: a.name == c.addon, self.addons))
            if len(addons) == 1:
                if addons[0] not in all_addons:
                    all_addons[addons[0]] = []
                all_addons[addons[0]].append(c)
        return all_addons

    def drop_context(self, addon, msg_id=None, user=None, chat=None):
        context = self._retrieve_context(addon.name, msg_id, user, chat)
        context.delete()

    def send_message(self, chat, text=None, origin_user=None, reply_to=None,
                     markup=None, disable_preview=False,
                     payload={}, force=False, mute=False, parse_mode=None):
        if not force and not (self.get_activity(chat.telegram_id) and
                              self.get_activity_global()):
            logging.warning(
                "Trying to send message to an"
                " inactive chat or by inactive bot")
            return
        counter = 0
        print("SENDING FROM {}".format(self.name))
        all_sent = []
        while counter <= GLOBAL_MSG_TRY_LIMIT:
            try:
                if text is not None:
                    msgs = self.trim_message(text)
                    for m in msgs:
                        sent = self.bot.send_message(
                            chat.telegram_id, m,
                            disable_web_page_preview=disable_preview,
                            reply_markup=markup,
                            reply_to_message_id=reply_to,
                            disable_notification=mute,
                            parse_mode=parse_mode)
                    all_sent.append(sent)
                if "STICKER" in payload:
                    sent = self.bot.send_sticker(chat.telegram_id,
                                                 payload["STICKER"]["id"],
                                                 reply_markup=markup,
                                                 reply_to_message_id=reply_to,
                                                 disable_notification=mute)
                    all_sent.append(sent)
                if "AUDIO" in payload:
                    sent = self.bot.\
                        send_audio(chat.telegram_id,
                                   payload["AUDIO"]["file"],
                                   title=payload["AUDIO"]["title"],
                                   performer=payload["AUDIO"]["performer"],
                                   reply_markup=markup,
                                   reply_to_message_id=reply_to,
                                   disable_notification=mute)
                    all_sent.append(sent)
                if "VOICE" in payload:
                    sent = self.bot.\
                        send_voice(chat.telegram_id,
                                   payload["VOICE"]["file"],
                                   caption=payload["VOICE"]["title"],
                                   reply_markup=markup,
                                   reply_to_message_id=reply_to,
                                   disable_notification=mute)
                    all_sent.append(sent)
                if "PHOTO" in payload:
                    sent = self.bot.\
                        send_photo(chat.telegram_id,
                                   payload["PHOTO"]["file"],
                                   caption=payload["PHOTO"]["title"],
                                   reply_markup=markup,
                                   reply_to_message_id=reply_to,
                                   disable_notification=mute)
                    all_sent.append(sent)
                if "LOCATION" in payload:
                    sent = self.bot.\
                        send_location(chat.telegram_id,
                                      latitude=payload["LOCATION"]["lat"],
                                      longitude=payload["LOCATION"]["long"],
                                      reply_markup=markup,
                                      reply_to_message_id=reply_to,
                                      disable_notification=mute)
                    all_sent.append(sent)
                if "DOCUMENT" in payload:
                    sent = self.bot.\
                        send_document(chat.telegram_id,
                                      payload["DOCUMENT"]["file"],
                                      caption=payload["DOCUMENT"]["title"],
                                      reply_markup=markup,
                                      reply_to_message_id=reply_to,
                                      disable_notification=mute)
                    all_sent.append(sent)
                if "VIDEO" in payload:
                    if payload["VIDEO"]["type"] == "note":
                        sent = self.bot.\
                            send_video_note(chat.telegram_id,
                                            payload["VIDEO"]["file"],
                                            reply_markup=markup,
                                            reply_to_message_id=reply_to,
                                            disable_notification=mute)
                    else:
                        sent = self.bot.\
                            send_video(chat.telegram_id,
                                       payload["VIDEO"]["file"],
                                       caption=payload["VIDEO"]["title"],
                                       reply_markup=markup,
                                       reply_to_message_id=reply_to,
                                       disable_notification=mute)
                    all_sent.append(sent)
                if "CONTACT" in payload:
                    sent = self.bot.send_sticker(chat.telegram_id,
                                                 payload["CONTACT"]["phone"],
                                                 payload["CONTACT"]["first"],
                                                 payload["CONTACT"]["last"],
                                                 reply_markup=markup,
                                                 reply_to_message_id=reply_to,
                                                 disable_notification=mute)
                    all_sent.append(sent)              
                for s in all_sent:
                    self._log_message(s, origin_user)
                return all_sent
            except Exception as e:
                print(e)
                counter += 1
            return None

    def get_user(self, user):
        try:
            db_user = self.models["Users"].objects.get(
                bot__name=self.name, telegram_id=user.id)
        except self.models["Users"].DoesNotExist:
            db_user = self.models["Users"]()
            db_user.bot = self.db_bot
            db_user.telegram_id = user.id
            db_user.first_name = user.first_name
            db_user.last_name = user.last_name
            db_user.user_name = user.username
            db_user.init_date = datetime.datetime.utcnow()
            db_user.lang = user.language_code
            if user.username in self.preset_roles:
                db_user.role = self.preset_roles[user.username]
            else:
                db_user.role = "USER"
            db_user.save()
        return db_user

    def get_chat(self, chat):
        try:
            db_chat = self.models["Chats"].objects.get(
                bot__name=self.name, telegram_id=chat.id)
        except self.models["Chats"].DoesNotExist:
            db_chat = self.models["Chats"]()
            db_chat.bot = self.db_bot
            db_chat.telegram_id = chat.id
            db_chat.chat_type = chat.type
            if db_chat.chat_type == "private":
                db_chat.first_name = chat.first_name
                db_chat.last_name = chat.last_name
            else:
                db_chat.title = chat.title
            db_chat.user_name = chat.username
            db_chat.is_active = False
            db_chat.init_date = datetime.datetime.utcnow()
            db_chat.save()
        return db_chat

    def check_user_and_chat(self, message):
        db_user = self.get_user(message.from_user)
        db_chat = self.get_chat(message.chat)
        return db_chat, db_user

    def trigger_task(self, task, task_model):
        print(task.addon, task.command)
        for a in self.addons:
            if a.name == task.addon:
                for t in a.tasks:
                    if t.name == task.command:
                        # returning False means "delete the task"
                        # if the task is updated, return True
                        # WARNING:
                        # Not updated task with True returned will be triggered
                        # INFINITELY!
                        res = t.call(task, task_model)
                        return res
        return False

    def check_tasks(self):
        db_tasks = self.models["Tasks"].objects.filter(bot__name=self.name)
        to_do = []
        for t in db_tasks:
            if t.trigger_time.replace(tzinfo=None) <= \
              datetime.datetime.utcnow():
                to_do.append(t)
        for t in to_do:
            if not self.trigger_task(t, self.models["Tasks"]):
                print("Received false - deleting task")
                t.delete()

    # Get all tasks of a kind
    def get_task(self, chat, addon_name, command):
        return self.models["Tasks"].objects.filter(bot__name=self.name,
                                                   chat=chat,
                                                   addon=addon_name,
                                                   command=command)

    # Current task is deleted after being triggered
    # Tasks model and current task are passed to function,
    # so that the latter can reset task
    # By default, only one task of a kind is allowed for a chat
    # "allow_multiple" argument allows to override this
    # Otherwise, only the time will be modified
    def add_task(self, trigger_time, db_chat, addon_name, command,
                 description, db_user, args={},
                 allow_multiple=False, random_reset=False):
        if not trigger_time:
            trigger_time = datetime.datetime.utcnow() + \
                datetime.timedelta(seconds=30)
        if not allow_multiple:
            test = self.get_task(db_chat, addon_name, command)
            if test.count() > 0:
                task = test.get()
                task.trigger_time = trigger_time
                task.time = datetime.datetime.utcnow()
                task.set_by = db_user
                task.save()
                return False
        task = self.models["Tasks"]()
        task.bot = self.db_bot
        task.chat = db_chat
        task.random_time = random_reset
        task.trigger_time = trigger_time
        task.time = datetime.datetime.utcnow()
        task.description = description
        task.args = json.dumps(args)
        task.set_by = db_user
        task.addon = addon_name
        task.command = command
        task.counter = 0
        task.save()
        return True

    # Delete tasks
    # Currently, most precise filter is "chat + addon + command",
    # that means all such tasks will be deleted
    # Addon and command argumets are optional,
    # lack of those will delete all the tasks for current chat
    def delete_task(self, db_chat, addon_name=None, command=None):
        if addon_name is not None:
            if command is not None:
                self.get_task(db_chat, addon_name, command).delete()
            else:
                self.models["Tasks"].objects.filter(bot__name=self.name,
                                                    chat=db_chat,
                                                    addon=addon_name).delete()
        else:
            self.models["Tasks"].objects.filter(bot__name=self.name,
                                                chat=db_chat).delete()

    # Resets task
    # Period or new time can be provided
    # If new time provided, it is being checked
    # Unless it is later, than current time,
    # it will be set 30 seconds after current time
    # If no new time present, delta is added to initial time
    # If none present, delta is considered 24 hours
    def reset_task(self, task, delta=None, new_time=None):
        if new_time is None:
            if delta is None:
                new_time = task.trigger_time + datetime.timedelta(hours=24)
                if task.random_time:
                    new_time = new_time.replace(hour=random.randint(0, 24),
                                                minute=random.randint(0, 59))
            else:
                new_time = task.trigger_time + delta
        if new_time.replace(tzinfo=None) < datetime.datetime.utcnow():
            new_time = datetime.datetime.utcnow() + \
                datetime.timedelta(seconds=30)
        print("Resetting task {} from {} to {}".format(task.command,
                                                       task.trigger_time,
                                                       new_time))
        task.trigger_time = new_time
        task.counter += 1
        task.save()

    def declare(self):
        self.declared = True

        # Receiving commands
        @self.bot.message_handler(commands=self.commands_cache)
        def process_commands(message):
            print("COMMAND RECEIVED by {}".format(self.name))
            db_chat, db_user = self.check_user_and_chat(message)
            for ent in message.entities:
                if ent.type == "bot_command":
                    offs = ent.offset
                    ln = ent.length
                if (ln is not None) and (offs is not None):
                    cmd = message.text[offs + 1:ln].split('@')[0]
                    logging.info(
                        "User {} {} ({}) triggered a {} command".format(
                            db_user.first_name, db_user.last_name,
                            db_user.telegram_id, cmd))
                    args = message.text[ln+1:]
                    break
            command, addon = self.get_command(cmd)
            if command is None:
                logging.error("{} was triggered but not found".format(cmd))
                return False
            command.call(db_user, db_chat, message, args)
            return True

        @self.bot.message_handler(
                func=lambda message:
                message.reply_to_message is not None and
                message.reply_to_message.from_user.id == 
                self.db_bot.telegram_id,
                content_types=["photo", "text", "location"])
        def process_reply(message):
            print("PROCESSING REPLY")
            db_chat, db_user = self.check_user_and_chat(message)
            all_addons = self._get_addons_by_context(message.reply_to_message,
                                                     db_user, db_chat)
            for a in all_addons:
                for c in all_addons[a]:
                    a.process_reply(c, db_user, db_chat, message)
            return True

        @self.bot.callback_query_handler(func=lambda call: True)
        def process_callback(call):
            for a in self.addons:
                for c in a.callbacks:
                    if c.cb == call.data:
                        c.call(self.get_user(call.from_user),
                               self.get_chat(call.message.chat),
                               call)
                        return True
            logging.error(
                "{} callback was received but not found".format(call.data))
            return False
