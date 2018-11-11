from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError
from rpfti.apps import get_bot
import telebot
import traceback, sys

cntr = 0
mainbot = None


def mon(request):
    return HttpResponse("Monitoring site will be here {}".format(cntr))


@csrf_exempt
def bot(request):
    update = "No update detected"
    try:
        global mainbot
        if mainbot is None:
            print("DECLARING")
            mainbot = get_bot()
            # mainbot.declare()
        json_string = request.body.decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        mainbot.bot.process_new_updates([update])
    except Exception as e:
        print("---EXCEPTION---")
        traceback.print_exc(limit=2, file=sys.stdout)
        print("DURING REQUEST: {}".format(update))
        return HttpResponseServerError()
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
