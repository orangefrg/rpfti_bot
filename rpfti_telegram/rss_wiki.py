import requests
import datetime
import lxml.html as html
import re
import random

months = ["января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября",
          "декабря"]

annivs = [1000, 500, 250, 100, 50, 5]

def get_events(marker, doc):
    event_tags = []
    catch_tag = False
    for c in doc.getchildren():
        if not catch_tag and c.tag != "h2":
            continue
        elif c.tag == "h2" and c.getchildren()[0].text == marker:
            catch_tag = True
        elif catch_tag and c.tag == "ul":
            event_tags.extend(c.getchildren())
        elif catch_tag and c.tag == "h2":
            break

    out_strings = []
    for t in event_tags:
        year = None
        out_string = str(t.text) if t.text is not None else ""
        for chld in t.getchildren():
            if year is None:
                year_str = chld.text
                year_m = re.search("(\d+)", year_str)
                if year_m is None:
                    break
                year = year_m.group(0)
                bc_m = re.search("до", year_str)
                if bc_m is not None:
                    year = -int(year)
                else:
                    year = int(year)
                if chld.tail is not None:
                    out_string += str(chld.tail)
                continue
            elif chld.tag == "ul":
                for ic in chld.getchildren():
                    out_string = ""
                    out_string += str(ic.text) if ic.text is not None else ""
                    for icc in ic.getchildren():
                        if icc.text is not None:
                            out_string += str(icc.text)
                        if icc.tail is not None:
                            out_string += str(icc.tail)
                    out_string = " — " + out_string
                    out_strings.append((year, year_str, out_string))
            else:
                if chld.text is not None:
                    out_string += str(chld.text)
                if chld.tail is not None:
                    out_string += str(chld.tail)
        if year is not None:
            out_strings.append((year, year_str, out_string))
    return out_strings

def get_names(doc):
    name_tags = []
    catch_tag = False
    for c in doc.getchildren():
        if not catch_tag and c.tag != "h3" and c.tag != "h2":
            continue
        elif (c.tag == "h3" or c.tag == "h2") and c.getchildren()[0].text == "Именины":
            catch_tag = True
        elif catch_tag:
            if c.tag == "ul":
                name_tags.extend(c.getchildren())
            elif c.tag in ["h2", "h3"]:
                break
    out_string = ""
    for t in name_tags:
        if t.text is not None:
            out_string += t.text
        for c in t.getchildren():
            if c.text is not None:
                out_string += str(c.text)
            if c.tail is not None:
                out_string += str(c.tail)
        out_string += "\n"
    return out_string


def sort_by_anniversaries(array, limit, cur_year, anniv_order=0):
    out_elements = []
    if anniv_order < len(annivs):
        for a in array:
            if limit == 0:
                break
            diff = cur_year - a[0]
            if diff % annivs[anniv_order] == 0:
                new_elem = a + (diff,)
                out_elements.append(new_elem)
                array.remove(a)
                limit -= 1
        if limit > 0 and len(array) > 0:
            out_elements.extend(sort_by_anniversaries(array, limit, cur_year, anniv_order + 1))
    else:
        while limit > 0 and len(array) > 0:
            elem = random.choice(array)
            diff = cur_year - elem[0]
            new_elem = elem + (diff,)
            out_elements.append(new_elem)
            array.remove(elem)
            limit -= 1
    return out_elements


def diff_to_string(diff):
    if diff % 10 in [2, 3, 4] and diff % 100 not in [12, 13, 14]:
        year_str = "года"
    elif diff % 10 == 1 and diff % 100 != 11:
        year_str = "год"
    else:
        year_str = "лет"
    return "{} {} назад".format(diff, year_str)


def prepare_string(cur_date, events, born, died, names):
    out_string = "<b>{} {} в истории</b>\n\n".format(cur_date.day, months[cur_date.month-1])
    if len(names) > 0:
        out_string += "<b>Именины</b>:\n"
        out_string += names
    if len(born) > 0:
        out_string += "\n<b>В этот день родились:</b>\n"
        for e in born:
            out_string += "{} ({}){}\n".format(diff_to_string(e[3]), e[1], e[2])
    if len(died) > 0:
        out_string += "<b>И умерли:</b>\n"
        for e in died:
            out_string += "{} ({}){}\n".format(diff_to_string(e[3]), e[1], e[2])
    if len(events) > 0:
        out_string += "<b>События в истории:</b>\n"
        for e in events:
            out_string += "{} ({}){}\n".format(diff_to_string(e[3]), e[1], e[2])
    return out_string




def read_todays_events(date=None, limit=5):
    cur = datetime.datetime.utcnow() if date is None else date
    link = "https://ru.wikipedia.org/wiki/{}_{}".format(cur.day, months[cur.month - 1])
    r = requests.get(link)
    doc = html.document_fromstring(r.content.decode("utf-8", "strict")).find_class('mw-parser-output').pop()
    names = get_names(doc)
    events = sorted(sort_by_anniversaries(get_events("События", doc), limit, cur.year), key = lambda elem: elem[0])
    born = sorted(sort_by_anniversaries(get_events("Родились", doc), limit, cur.year), key = lambda elem: elem[0])
    died = sorted(sort_by_anniversaries(get_events("Скончались", doc), limit, cur.year), key = lambda elem: elem[0])
    return prepare_string(cur, events, born, died, names)