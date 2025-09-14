import json


in_dir = "comparation/"
out_dir = "human_check/"
file = "troops"

with open("GLOSSARY" + ".json", "r", encoding="utf-8") as f:
    glossary = json.load(f)


with open(in_dir + file + ".json", "r", encoding="utf-8") as f:
    data = json.load(f)
    res = {}
    for _, original, _, translation in data:
        glossary: dict
        replace = glossary.get(original, translation)
        res[original] = replace

with open(out_dir + file + ".json", "w", encoding="utf-8") as f:
    json.dump(res, f, ensure_ascii=False, indent=2)
