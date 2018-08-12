import requests
import json

def get_data(url, request_settings_dict, ignore_bad_certificate=False):
    request_string = json.dumps(request_settings_dict)
    request_data = {
        "settings": request_string
    }
    r = requests.post(url, request_data, verify=(not ignore_bad_certificate))
    result = {}
    result["code"] = r.status_code
    if r.status_code == 200:
        result["payload"] = r.json()
        result["status"] = "OK"
    else:
        result["status"] = "ERROR"
    return result
