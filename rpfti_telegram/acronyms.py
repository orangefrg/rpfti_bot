import os, random, re, sys

big_arr = []
words_adj = []

valid_acronym_banned = ["Ы", "Ь", "Ъ"]

cached_acronyms = {}
cached_acronyms_adj = {}

def loadwords():
    global big_arr
    global words_adj
    path = os.path.dirname(os.path.abspath(__file__))
    f_male = open(path + "/words/dict.male")
    f_female = open(path + "/words/dict.female")
    f_indef = open(path + "/words/dict.indef")
    f_adj = open(path + "/words/dict.adj")
    words_male = f_male.readlines()
    words_female = f_female.readlines()
    words_indef = f_indef.readlines()
    words_adj = f_adj.readlines()
    big_arr = {'male': words_male,
               'female': words_female, 'indef': words_indef}


def gender_change(word, gender):
    if gender == 'female':
        word = re.sub("(\S+)([с|н])ий$", "\g<1>\g<2>яя", word)
        word = re.sub("(\S+)([и|ы|о]й)$", "\g<1>ая", word)
        word = re.sub("(\S+)([н|в])$", "\g<1>\g<2>а", word)
        word = re.sub("(\S+)([ий|ый|ой]ся)$", "\g<1>аяся", word)
    elif gender == 'indef':
        word = re.sub("(\S+)([с|н])ий$", "\g<1>\g<2>ее", word)
        word = re.sub("(\S+)([и|ы|о]й)$", "\g<1>ое", word)
        word = re.sub("(\S+)([н|в])$", "\g<1>\g<2>о", word)
        word = re.sub("(\S+)([ий|ый|ой]ся)$", "\g<1>ееся", word)
    return word


def get_random_noun():
    key = random.choice(list(big_arr.keys()))
    selected_words = big_arr[key]
    noun = random.choice(selected_words)
    return key, noun


def get_random_adj(gender):
    adj = gender_change(random.choice(words_adj), gender)
    return adj


def acronym_preprocessing(acronym):
    acronym_parts = []
    all_upper = False
    for a in acronym:
        if bool(re.search('[а-яА-Я]', a)):
            if all_upper:
                a = a.upper()
            if a.islower():
                if len(acronym_parts) > 0:
                    acronym_parts[-1] += a
                elif a.upper() not in valid_acronym_banned:
                    acronym_parts.append(a.upper())
                    all_upper = True
            elif a not in valid_acronym_banned:
                acronym_parts.append(a)
    print(acronym_parts)
    return acronym_parts


def get_acronym_definition_noun(acronym_part):
    global big_arr
    global cached_acronyms
    acronym_part = acronym_part.lower()
    matching_words = []
    if acronym_part in cached_acronyms:
        matching_words = cached_acronyms[acronym_part]
    else:
        for gender in big_arr:
            for word in big_arr[gender]:
                if re.match("{}(.*)".format(acronym_part), word):
                    matching_words.append((word, gender))
        cached_acronyms[acronym_part] = matching_words
    if len(matching_words) == 0:
        return None
    return matching_words


def get_acronym_definition_adj(acronym_part, gender):
    global big_arr
    global cached_acronyms_adj
    acronym_part = acronym_part.lower()
    matching_words = []
    if acronym_part in cached_acronyms_adj:
        matching_words = cached_acronyms_adj[acronym_part]
    else:
        for word in words_adj:
            if re.match("{}(.*)".format(acronym_part), word):
                matching_words.append(word)
        cached_acronyms[acronym_part] = matching_words
    if len(matching_words) == 0:
        return None
    return [gender_change(w, gender) for w in matching_words]


def get_acronym_as_motto(acronym_parts):
    global big_arr
    definition = []
    for p in acronym_parts:
        matching_words = get_acronym_definition_noun(p)
        part_def = random.choice(matching_words)
        if p is None:
            return None
        definition.append(part_def[0])
    out_str = ""
    if len(definition) > 1:
        out_str += definition[0][0].upper() + definition[0][1:].strip() + ": "
        out_str += ", ".join([w.strip() for w in definition[1:]])
        out_str += "!"
    else:
        out_str = definition[0][0].upper() + definition[0][1:].strip() + "!"
    return out_str


def get_acronym_standard(acronym_parts):
    acronym_scheme = []
    acronym_definition = []
    out_str = ""
    if len(acronym_parts) == 1:
        matching_words = get_acronym_definition_noun(acronym_parts[0])
        if matching_words is None:
            return None
        out_str = random.choice(matching_words)[0]
        return out_str
    acronym_scheme.append((acronym_parts[-1], "noun"))
    for part in reversed(acronym_parts[:-1]):
        if random.randrange(100) >= 50:
            acronym_scheme.append((part, "noun"))
        else:
            acronym_scheme.append((part, "adj"))
    last_gender = ""
    for scheme_part in acronym_scheme:
        if scheme_part[1] == "noun":
            matching_words = get_acronym_definition_noun(scheme_part[0])
            if matching_words is None:
                return None
            selection = random.choice(matching_words)
            if len(acronym_definition) > 0:
                acronym_definition[-1] = acronym_definition[-1][0].upper() + acronym_definition[-1][1:]
            acronym_definition.append(selection[0].strip() + ".")
            last_gender = selection[1]
        elif scheme_part[1] == "adj":
            matching_words = get_acronym_definition_adj(scheme_part[0], last_gender)
            acronym_definition.append(random.choice(matching_words).strip())
    out_str = " ".join(reversed(acronym_definition))
    out_str = out_str[0].upper() + out_str[1:]
    return out_str
    

loadwords()
acr = sys.argv[1]
parts = acronym_preprocessing(acr)
print(get_acronym_as_motto(parts))
print(get_acronym_standard(parts))
