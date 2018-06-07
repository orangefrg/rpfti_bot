from django.db import models
from .bot_basic import *

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