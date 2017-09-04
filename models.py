from django.db import models

USER_ROLES = (
    ("ADMIN", "Administrator"),
    ("EDIT", "Editor"),
    ("MOD", "Moderator"),
    ("USER", "Simple user"),
    ("BAN", "Banned user")
)

CHAT_TYPES = (
    ("private", "Private chat"),
    ("group", "Group chat"),
    ("supergroup", "Supergroup"),
    ("channel", "Channel")
)

CONTENT_TYPES = (
    ("PLAIN", "Plain text"),
    ("STICKER", "Sticker"),
    ("AUDIO", "Audio file"),
    ("VOICE", "Voice message"),
    ("PHOTO", "Photo or image"),
    ("LOCATION", "Location"),
    ("DOCUMENT", "Document or file"),
    ("VIDEO", "Video file"),
    ("CONTACT", "Contact information")
)


class Bot(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True)
    is_active = models.BooleanField(default=False)
    start_time = models.DateTimeField()


class TelegramUser(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    telegram_id = models.IntegerField()
    first_name = models.CharField(max_length=200, null=True)
    last_name = models.CharField(max_length=200, null=True)
    user_name = models.CharField(max_length=200, null=True)
    init_date = models.DateTimeField()
    role = models.CharField(max_length=5, choices=USER_ROLES, default="USER")
    lang = models.CharField(max_length=100, null=True)


class TelegramChat(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    telegram_id = models.IntegerField()
    first_name = models.CharField(max_length=200, null=True)
    last_name = models.CharField(max_length=200, null=True)
    user_name = models.CharField(max_length=200, null=True)
    title = models.CharField(max_length=500, null=True)
    init_date = models.DateTimeField()
    chat_type = models.CharField(max_length=20, choices=CHAT_TYPES)
    is_active = models.BooleanField(default=False)


class Message(models.Model):
    message_id = models.IntegerField()
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    to_user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE,
                                null=True)
    chat = models.ForeignKey(TelegramChat, on_delete=models.CASCADE)
    date = models.DateTimeField()
    text = models.TextField(null=True)
    content = models.CharField(max_length=20, choices=CONTENT_TYPES)
    content_id = models.CharField(max_length=200, null=True)


class Like(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    liked_by = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    date = models.DateTimeField()


class ScheduledTask(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    chat = models.ForeignKey(TelegramChat, on_delete=models.CASCADE)
    time = models.DateTimeField()
    trigger_time = models.DateTimeField()
    description = models.TextField()
    args = models.TextField()
    set_by = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    addon = models.CharField(max_length=200)
    command = models.CharField(max_length=200)
    counter = models.IntegerField()
