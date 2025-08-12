import json

# 用于把 text 中的有关数据导出为 json


def is_number(s):
    try:
        int(s)  # 或 float(s) 如果需要支持小数
        return True
    except ValueError:
        return False


def conversation(f):
    next(f)
    next(f)
    for line in f:
        key, *texts = line.split()
        for text in texts:
            if is_number(text):
                continue
            if text == "NO_VOICEOVER":
                break
            if text.startswith("{!}"):
                continue
            if text.strip():
                res[key] = text.strip()


def game_string(f):
    next(f)
    next(f)
    key = ""
    for line in f:
        line: str
        texts: list[str] = line.strip().split()
        if len(texts) != 2:
            print("game string len is not 2")
            print(len(texts))
            continue
        if  texts[1].strip().startswith('{!}'):
            continue
        res[texts[0].strip()] = texts[1].strip()


def game_menu(f):
    next(f)
    next(f)
    last_key = ""
    for line in f:
        line: str
        key = ""
        texts: list[str] = line.strip().split()
        for text in texts:
            if is_number(text):
                continue
            if text == "." or text == "none" or text == "_":
                continue
            if len(key) == 0:
                if text.startswith("mno") == False and text.startswith("menu") == False:
                    key = last_key + "_door"
                    res[key] = text.strip()
                    last_key = key
                    key = ""
                else:
                    key = text.strip()
                continue
            else:
                if res.get(key) is None and text.startswith("{!}") == False:
                    res[key] = text.strip()
                    last_key = key
                key = ""


def info_pages(f):
    next(f)
    next(f)
    for line in f:
        key, title, article = line.strip().split(maxsplit=2)

        res[key] = title.strip()
        res[key + "_text"] = article.strip()


def item_kinds(f):
    next(f)
    next(f)
    for line in f:
        if len(line) < 10:
            continue
        key, name, plural, _ = line.strip().split(maxsplit=3)
        if is_number(key):
            continue
        res[key] = name.strip()
        res[key + "_pl"] = plural.strip()


def party_templates(f):
    next(f)
    next(f)
    for line in f:
        key, name, _ = line.strip().split(maxsplit=2)
        name: str
        if name.startswith("{!}"):
            continue
        res[key] = name.strip()


def quick_string(f):
    next(f)
    for line in f:
        key, name = line.strip().split(maxsplit=1)
        if name.startswith("{!}") == False:
            res[key] = name.strip()


def quest(f):
    next(f)
    next(f)
    for line in f:
        line: str
        key, name, _, desc = line.strip().split(maxsplit=3)

        res[key] = name.strip()
        if desc.startswith("{!}") == False:
            res[key + "_text"] = desc.strip()


def skill(f):
    next(f)
    for line in f:
        line: str
        key, name, _, _, desc = line.strip().split(maxsplit=4)

        if name.startswith("Reserved_Skill") == False:
            res[key] = name.strip()
            res[key + "_desc"] = desc.strip()


def troop(f):
    next(f)
    next(f)
    for line in f:
        line: str
        key, name, plural, _ = line.strip().split(maxsplit=3)
        if name.startswith("{!}") == False:
            res[key] = name.strip()
        if plural.startswith("{!}") == False and  plural!="_":
            res[key + "_pl"] = plural.strip()
        next(f)
        next(f)
        next(f)
        next(f)
        next(f)
        next(f)


in_dir = "eng/"
out_dir = "dumptxt/"
res = {}
with open(in_dir + "conversation" + ".txt", "r", encoding="utf-8") as f:
    conversation(f)
    with open(out_dir + "dialogs" + ".json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    res.clear()

with open(in_dir + "menus" + ".txt", "r", encoding="utf-8") as f:
    game_menu(f)
    with open(out_dir + "game_menus" + ".json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    res.clear()

with open(in_dir + "strings" + ".txt", "r", encoding="utf-8") as f:
    game_string(f)
    with open(out_dir + "game_strings" + ".json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    res.clear()

with open(in_dir + "info_pages" + ".txt", "r", encoding="utf-8") as f:
    info_pages(f)
    with open(out_dir + "info_pages" + ".json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    res.clear()

with open(in_dir + "item_kinds1" + ".txt", "r", encoding="utf-8") as f:
    item_kinds(f)
    with open(out_dir + "item_kinds" + ".json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    res.clear()

with open(in_dir + "party_templates" + ".txt", "r", encoding="utf-8") as f:
    party_templates(f)
    with open(out_dir + "party_templates" + ".json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    res.clear()

with open(in_dir + "quests" + ".txt", "r", encoding="utf-8") as f:
    quest(f)
    with open(out_dir + "quests" + ".json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    res.clear()

with open(in_dir + "quick_strings" + ".txt", "r", encoding="utf-8") as f:
    quick_string(f)
    with open(out_dir + "quick_strings" + ".json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    res.clear()

with open(in_dir + "skills" + ".txt", "r", encoding="utf-8") as f:
    skill(f)
    with open(out_dir + "skills" + ".json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    res.clear()

with open(in_dir + "troops" + ".txt", "r", encoding="utf-8") as f:
    troop(f)
    with open(out_dir + "troops" + ".json", "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    res.clear()
