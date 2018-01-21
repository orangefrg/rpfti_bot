from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseNotFound
from rpfti.apps import get_bot
import telebot

cntr = 0
mainbot = None


def mon(request):
    return HttpResponse("Monitoring site will be here {}".format(cntr))


@csrf_exempt
def bot(request):
    try:
        global mainbot
        if mainbot is None:
            print("DECLARING")
            mainbot = get_bot()
            # mainbot.declare()
        json_string = request.body.decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        mainbot.bot.process_new_updates([update])
    except:
        return HttpResponseNotFound()
    return HttpResponse()

@csrf_exempt
def control(request):
    try:
        global mainbot
        if mainbot is None:
            print("DECLARING")
            mainbot = get_bot()
            # mainbot.declare()
        json_string = request.body.decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        mainbot.bot.process_new_updates([update])
    except:
        return HttpResponseNotFound()
    return HttpResponse()

@csrf_exempt
def control(request):
    return HttpResponseNotFound()
