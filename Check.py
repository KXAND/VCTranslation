# 由 chatgpt生成
import asyncio
import json
import os
from openai import AsyncOpenAI
import aiofiles
import sys_prompt

# === 1. 配置 ===
SOURCE_FILE = "eng/parties.txt"
RESULT_FILE = "Qwen2.5-72B-Instruct-128K/parties.csv"
CACHE_FILE = "translation_cache.json"  # 缓存文件
GLOSSARY_FILE = "GLOSSARY.json"  # 缓存文件

dump_dir = "dumptxt/"
old_trans_dir = "work_cns/"
out = "comparation/"


def combine():

    for json_file in os.listdir(dump_dir):
        path = dump_dir + json_file
        com = []
        with open(path, "r", encoding="utf-8") as f:
            content = json.load(f)
            filename = json_file.split(".")[0]
        path = old_trans_dir + filename + ".csv"
        with open(path, "r", encoding="utf-8-sig") as f:
            trans = {}
            for line in f:
                a, b = line.split("|", 1)
                trans[a.strip()] = b.strip()
        for key, val in content.items():
            tran = trans.get(key)
            if tran is None:
                tran = ""
            com.append([key, val, tran])
        with open(out + filename + ".json", "w", encoding="utf-8") as f:
            json.dump(com, f, ensure_ascii=False, indent=2)


async def main():
    # 从文件读取（你也可以改成直接传字符串）
    tuples = []
    not_info_line = False
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        source_pairs: dict = {}
        for line in f:
            if not_info_line:
                not_info_line = False
                continue

            [_, _, _, _, key, text, _] = line.split(" ", 6)
            not_info_line = True
            if text.strip():
                source_pairs[text.strip()] = key
    cache = {}
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r", encoding="utf-8") as f:
            cache = json.load(f)
    old = {}
    with open("work_cns\\parties.csv", "r", encoding="utf-8") as f:
        for line in f:
            key, name = line.split("|", 1)
            old[key] = name
    for e in cache:
        id = source_pairs[e]
        if id in old:
            tuples.append((id, e, cache[e], old[id].strip()))

    with open("work_cns\\compare.json", "w", encoding="utf-8") as f:
        json.dump(tuples, f, ensure_ascii=False, indent=2)


# === 4. 示例使用 ===
if __name__ == "__main__":
    # asyncio.run(main())
    combine()
