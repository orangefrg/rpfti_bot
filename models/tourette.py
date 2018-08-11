from django.db import models
from .bot_basic import *

class TouretteUser(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    tlg_chat = models.ForeignKey(TelegramChat, on_delete=models.CASCADE)
    tlg_user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE,
                                null=True)
    count = models.IntegerField()
    

    def __str__(self):
        return "{0.tlg_user.first_name} ({0.tlg_chat.title})".format(self)
