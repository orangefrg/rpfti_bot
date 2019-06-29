from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, HttpResponseNotFound, HttpResponseServerError
from rpfti.apps import get_whoami, get_infobot, get_amoralbot
import telebot
import traceback, sys

cntr = 0
whoamibot = None
infobot = None
amoralbot = None


def mon(request):
    return HttpResponse("Monitoring site will be here {}".format(cntr))


@csrf_exempt
def wai(request):
    update = "No update detected"
    try:
        global whoamibot
        if whoamibot is None:
            print("DECLARING WAI")
            whoamibot = get_whoami()
        json_string = request.body.decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        whoamibot.bot.process_new_updates([update])
    except Exception as e:
        print("---EXCEPTION WAI---")
        traceback.print_exc(limit=2, file=sys.stdout)
        print("DURING REQUEST: {}".format(update))
        return HttpResponseServerError()
    return HttpResponse()

@csrf_exempt
def info(request):
    update = "No update detected"
    try:
        global infobot
        if infobot is None:
            print("DECLARING INFO")
            infobot = get_infobot()
        json_string = request.body.decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        infobot.bot.process_new_updates([update])
    except Exception as e:
        print("---EXCEPTION INFO---")
        traceback.print_exc(limit=2, file=sys.stdout)
        print("DURING REQUEST: {}".format(update))
        return HttpResponseServerError()
    return HttpResponse()

@csrf_exempt
def amoral(request):
    update = "No update detected"
    try:
        global amoralbot
        if amoralbot is None:
            print("DECLARING AMORAL")
            amoralbot = get_amoralbot()
        json_string = request.body.decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        amoralbot.bot.process_new_updates([update])
    except Exception as e:
        print("---EXCEPTION AMORAL---")
        traceback.print_exc(limit=2, file=sys.stdout)
        print("DURING REQUEST: {}".format(update))
        return HttpResponseServerError()
    return HttpResponse()


