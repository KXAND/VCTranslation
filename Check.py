# 由 chatgpt生成
import asyncio
import json
import os
from openai import AsyncOpenAI
import aiofiles
import sys_prompt

# === 1. 配置 ===
API_KEY = "sk-velwkjvebxgxiqxjijitamirmmbagachcklcrygbeifujxnz"
BASE_URL = "https://api.siliconflow.cn/v1"
MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct-128K"  # 模型名
SOURCE_FILE = "eng/parties.txt"
RESULT_FILE = "Qwen2.5-72B-Instruct-128K/parties.csv"
CACHE_FILE = "translation_cache.json"  # 缓存文件
GLOSSARY_FILE = "GLOSSARY.json"  # 缓存文件
SOURCE_LANGUAGE = "English"
TARGET_LANGUAGE = "Chinese"
BATCH_SIZE = 200  # 每批处理行数
CONCURRENCY = 5  # 并发请求数


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
    asyncio.run(main())
