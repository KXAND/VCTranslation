import json


in_dir = "human_check/"
out_dir = "comparation/"
file = "troops"

with open(in_dir + file + ".json", "r", encoding="utf-8") as f:
    new_trans = json.load(f)

with open(out_dir + file + ".json", "r", encoding="utf-8") as f:
    data = json.load(f)
    new_data = []
    for id, eng,*_, translation in data:
        new_data.append([id, eng, translation, new_trans.get(eng, "")])

with open(out_dir + file + ".json", "w", encoding="utf-8") as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)
