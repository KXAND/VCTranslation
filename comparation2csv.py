import json
import os
import re

comparation_dir = "comparation\\"
csv_dir = "result\\"


def get_added_space_text(text: str):
    return re.sub(r"([\u4e00-\u9fa5。；，：“”（）、？《》！·…—])", r"\1 ", str(text))


def get_properly_punctuation_text(text: str):
    text = text.replace("(", "（")
    text = text.replace(")", "）")
    text = text.replace("[", "【")
    text = text.replace("]", "】")
    text = text.replace(",", "，")
    text = text.replace(": ", "：")
    text = text.replace(". ", "。")
    return text


for json_file in os.listdir(comparation_dir):
    with open(comparation_dir + json_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    with open(csv_dir + json_file.split(".")[0] + ".csv", "w", encoding="utf-8") as f:
        for id, eng, *_, translation in data:

            text = get_properly_punctuation_text(translation)
            text = get_added_space_text(text)
            f.write(f"{id}|{text}\n")
