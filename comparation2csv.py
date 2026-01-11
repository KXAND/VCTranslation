import json
import os
import re

comparation_dir = "comparation\\"
csv_dir = "cns\\"


def get_added_space_text(text: str):
    if not text:
        return ""

    text = str(text).replace(" ", "")  # 删除原有的空格
    # 1. 在每个“中文字符”后面添加一个空格
    # 范围：常用汉字 + 您列出的中文全角标点
    # 注意：这里会覆盖汉字与汉字、汉字与数字、汉字与行末的情况
    text = re.sub(r"([\u4e00-\u9fa5。；，：“”（）、？《》！·…—])", r"\1 ", text)

    # 2. 处理“数字/字母”与“汉字”交界的情况（针对 数字在前 的场景）
    # 如果数字/字母后面紧跟着一个汉字，则在中间插入空格
    # 逻辑：匹配 [字母数字] 且 后面跟着 [汉字]，并在两者间加空格
    text = re.sub(r"([a-zA-Z0-9])(?=[\u4e00-\u9fa5])", r"\1 ", text)

    # 3. 规范化空格（防止出现连续双空格）
    # 比如“汉字 123”原本已经有一个空格，上述逻辑可能导致变成“汉字  123”
    text = re.sub(r" +", " ", text)

    return text


def get_properly_punctuation_text(text: str):
    text = text.replace("(", "（")
    text = text.replace(")", "）")
    text = text.replace("[", "【")
    text = text.replace("]", "】")
    text = text.replace(",", "，")
    text = text.replace(": ", "：")
    text = text.replace(". ", "。")
    return text


aggregated_data = {}
for json_file in os.listdir(comparation_dir):
    with open(comparation_dir + json_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    key = json_file.split(".")[0]
    if key not in aggregated_data:
        aggregated_data[key] = []
    
    for entry in data:
        id = entry["id"]
        translation = entry["translation"]
        text = get_properly_punctuation_text(translation)
        text = get_added_space_text(text)
        aggregated_data[key].append({"id": id, "translation": text})

# 2. 第二步：将聚合后的数据写入对应的 CSV
for file_prefix, items in aggregated_data.items():
    csv_path = os.path.join(csv_dir, f"{file_prefix}.csv")

    # 使用 utf-8-sig 以便 Excel 正常打开中文，或者根据引擎要求使用 utf-8
    with open(csv_path, "w", encoding="utf-8") as f:
        for entry in items:
            # 写入格式 ID|内容
            entry_id = entry["id"]
            text = entry["translation"]
            f.write(f"{entry_id}|{text}\n")
