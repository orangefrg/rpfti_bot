import requests
import datetime
import lxml.html as html
import re
import random

months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября",
          "декабря"]

def get_events(marker, doc):
    event_tags = []
    catch_tag = False
    for c in doc.getchildren():
        if not catch_tag and c.tag != "h2":
            continue
        elif c.tag == "h2" and c.getchildren()[0].text == marker:
            catch_tag = True
        elif catch_tag:
            if c.tag == "ul":
                event_tags = c.getchildren()
                break

    out_strings = []
    for t in event_tags:
        year = None
        out_string = str(t.text) if t.text is not None else ""
        for chld in t.getchildren():
            if year is None:
                year = chld.text
                if chld.tail is not None:
                    out_string += str(chld.tail)
                continue
            elif chld.tag == "ul":
                for ic in chld.getchildren():
                    out_string = ""
                    out_string += str(ic.text) if ic.text is not None else ""
                    for icc in ic.getchildren():
                        out_string += str(icc.text) + str(icc.tail)
                    out_strings.append((year, out_string))
            else:
                out_string += str(chld.text) + str(chld.tail)
        out_strings.append((year, out_string))
    return out_strings

def get_names(doc):
    name_tags = []
    catch_tag = False
    for c in doc.getchildren():
        if not catch_tag and c.tag != "h3":
            continue
        elif c.tag == "h3" and c.getchildren()[0].text == "Именины":
            catch_tag = True
        elif catch_tag:
            if c.tag == "ul":
                name_tags.extend(c.getchildren())
            elif c.tag in ["h2", "h3"]:
                break
    out_strings = []
    for t in name_tags:
        out_strings.append(t.getchildren()[0].text)
    return ", ".join(out_strings)

def search_for_anniversaries(array, limit, cur_year):
    results = []
    for e in array:
        if len(results) < limit and len(array) > 0:
            year_m = re.search("(\d+)", e[0])
            year = year_m.group(0)
            bc_m = re.search("до", e[0])
            if bc_m is not None:
                passed = cur_year + int(year)
            else:
                passed = cur_year - int(year)
            if (passed >= 100 and passed % 10 == 0) or (passed < 100 and passed % 5 == 0):
                results.append((e[0], passed, e[1]))
                array.remove(e)
        else:
            break
    while len(results) < limit and len(array) > 0:
        e = random.choice(array)
        year_m = re.search("(\d+)", e[0])
        year = year_m.group(0)
        bc_m = re.search("до", e[0])
        if bc_m is not None:
            passed = cur_year + int(year)
        else:
            passed = cur_year - int(year)
        results.append((e[0], passed, e[1]))
        array.remove(e)
    out_strings = []
    for r in results:
        if r[1] % 100 == 1:
            yr_string = "год"
        elif r[1] % 10 in [2, 3, 4] and r[1] % 100 not in [12, 13, 14]:
            yr_string = "года"
        else:
            yr_string = "лет"
        string = "{} {} назад ({}) - {}".format(r[1], yr_string, r[0], r[2])
        out_strings.append(string)
    return out_strings

def read_todays_events(date=None, limit=10):
    cur = datetime.datetime.utcnow() if date is None else date
    link = "https://ru.wikipedia.org/wiki/{}_{}".format(cur.day, months[cur.month - 1])
    r = requests.get(link)
    doc = html.document_fromstring(r.content.decode("utf-8", "strict")).find_class('mw-parser-output').pop()
    names = get_names(doc)
    events = search_for_anniversaries(get_events("События", doc), limit, cur.year)
    born = search_for_anniversaries(get_events("Родились", doc), limit, cur.year)
    died = search_for_anniversaries(get_events("Скончались", doc), limit, cur.year)

    print(names)
    print(events)
    print(born)
    print(died)

    return(events, born, died, names)