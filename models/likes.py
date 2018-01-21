from .bot_basic import *
from django.db import models

class Like(models.Model):
    bot = models.ForeignKey(Bot, on_delete=models.CASCADE)
    message = models.ForeignKey(Message, on_delete=models.CASCADE)
    liked_by = models.ForeignKey(TelegramUser, on_delete=models.CASCADE)
    date = models.DateTimeField()
