import json
import os

# 用于把 text 中的有关数据导出为 json


def is_number(s):
    try:
        int(s)  # 或 float(s) 如果需要支持小数
        return True
    except ValueError:
        return False


def conversation(f):
    res = {}
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
    return res


def game_string(f):
    res = {}
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
        if texts[1].strip().startswith("{!}"):
            continue
        res[texts[0].strip()] = texts[1].strip()
    return res


def game_menu(f):
    res = {}
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
    return res


def info_pages(f):
    res = {}
    next(f)
    next(f)
    for line in f:
        key, title, article = line.strip().split(maxsplit=2)

        res[key] = title.strip()
        res[key + "_text"] = article.strip()
    return res


def item_kinds(f):
    res = {}
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
    return res


def parties(f):
    res = {}
    for line in f:
        line: str
        splits = line.strip().split()
        if len(splits) < 5:
            continue
        _, _, _, key, name, *_ = line.strip().split()
        name: str
        if name.startswith("{!}"):
            continue
        res[key] = name.strip()
    return res


def factions(f):
    res = {}
    for line in f:
        line: str
        splits = line.strip().split()
        if len(splits) > 5:
            continue
        _, key, name, *_ = line.strip().split()
        name: str
        if name.startswith("{!}"):
            continue
        res[key] = name.strip()
    return res


def party_templates(f):
    res = {}
    next(f)
    next(f)
    for line in f:
        key, name, _ = line.strip().split(maxsplit=2)
        name: str
        if name.startswith("{!}"):
            continue
        res[key] = name.strip()
    return res


def quick_string(f):
    res = {}
    next(f)
    for line in f:
        key, name = line.strip().split(maxsplit=1)
        if name.startswith("{!}") == False:
            res[key] = name.strip()
    return res


def quest(f):
    res = {}
    next(f)
    next(f)
    for line in f:
        line: str
        key, name, _, desc = line.strip().split(maxsplit=3)

        res[key] = name.strip()
        if desc.startswith("{!}") == False:
            res[key + "_text"] = desc.strip()
    return res


def skill(f):
    res = {}
    next(f)
    for line in f:
        line: str
        key, name, _, _, desc = line.strip().split(maxsplit=4)

        if name.startswith("Reserved_Skill") == False:
            res[key] = name.strip()
            res[key + "_desc"] = desc.strip()
    return res


def troop(f):
    res = {}
    next(f)
    next(f)
    for line in f:
        line: str
        key, name, plural, _ = line.strip().split(maxsplit=3)
        if name.startswith("{!}") == False:
            res[key] = name.strip()
        if plural.startswith("{!}") == False and plural != "_":
            res[key + "_pl"] = plural.strip()
        next(f)
        next(f)
        next(f)
        next(f)
        next(f)
        next(f)
    return res


in_dir = "eng/"
old_trans_dir = "cns/"
out_dir = "comparation/"

for filename in os.listdir(in_dir):
    combine = []
    # dump original content
    filename = filename.split(".")[0]
    with open(in_dir + filename + ".txt", "r", encoding="utf-8") as f:
        if filename == "factions":
            res = factions(f)
        elif filename == "parties":
            res = parties(f)
        elif filename == "troops":
            res = troop(f)
        elif filename == "skill":
            res = skill(f)
        elif filename == "quests":
            res = quest(f)
        elif filename == "party_templates":
            res = party_templates(f)
        elif filename == "item_kinds1":
            res = item_kinds(f)
        elif filename == "info_pages":
            res = info_pages(f)
        elif filename == "menus":
            res = game_menu(f)
        elif filename == "game_strings":
            res = game_string(f)
        elif filename == "conversation":
            res = conversation(f)
        elif filename == "quick_strings":
            res = quick_string(f)
        else:
            continue

    # Rename to match csv filenames
    if filename == "conversation":
        filename = "dialogs"
    elif filename == "menus":
        filename = "game_menus"
    elif filename == "strings":
        filename = "game_strings"
    elif filename == "item_kinds1":
        filename = "item_kinds"

    # read old translation from .csv
    with open(old_trans_dir + filename + ".csv", "r", encoding="utf-8-sig") as f:
        translation = {}
        for line in f:
            a, b = line.split("|", 1)
            translation[a.strip()] = b.strip().replace(" ", "")
    # combine
    for key, val in res.items():
        tran = translation.get(key)
        if tran is None:
            tran = ""
        combine.append([key, val, tran, ""])
   
    # 去重
    dict = {row[1]: row[2] for row in combine}
    items = list(dict.items())

    # 分块保存
    for i in range(0, len(items) // 500 + 1):
        with open(
            f"{out_dir}{filename.split('.')[0]}_{i}.json",
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(items[i : i + 500], f, ensure_ascii=False, indent=4)

