from .bot_basic import *
from django.db import models

class Context(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    addon = models.CharField(max_length=200)
    message = models.IntegerField()
    user = models.ForeignKey(TelegramUser, on_delete=models.CASCADE, null=True)
    chat = models.ForeignKey(TelegramChat, on_delete=models.CASCADE, null=True)
    context = models.TextField()