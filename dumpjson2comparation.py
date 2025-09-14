# 获取原始 comparation 文件（无AI翻译，仅原始翻译）
import asyncio
import json
import os
from openai import AsyncOpenAI
import aiofiles
import sys_prompt

# === 1. 配置 ===
SOURCE_FILE = "eng/parties.txt"
RESULT_FILE = "Qwen2.5-72B-Instruct-128K/parties.csv"

dump_dir = "dumptxt/"
old_trans_dir = "work_cns/"
out = "comparation/"


def combine():
    for json_file in os.listdir(dump_dir):
        com = []
        # read dumpped original content
        path = dump_dir + json_file
        with open(path, "r", encoding="utf-8") as f:
            content = json.load(f)
            filename = json_file.split(".")[0]

        # read old translation from .csv
        path = old_trans_dir + filename + ".csv"
        with open(path, "r", encoding="utf-8-sig") as f:
            trans = {}
            for line in f:
                a, b = line.split("|", 1)
                trans[a.strip()] = b.strip()

        # combine
        for key, val in content.items():
            tran = trans.get(key)
            if tran is None:
                tran = ""
            com.append([key, val, tran])
        
        # write
        with open(out + filename + ".json", "w", encoding="utf-8") as f:
            json.dump(com, f, ensure_ascii=False, indent=2)


# === 4. 示例使用 ===
if __name__ == "__main__":
    combine()
