# 由 chatgpt生成
import asyncio
import json
import os
from openai import AsyncOpenAI
import aiofiles
import sys_prompt
from key import _API_KEY

# === 1. 配置 ===
API_KEY = _API_KEY
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

files = [
    ("eng/conversation.txt", "aioutput/dialogs.csv"),
    ("eng/factions.txt", "aioutput/factions.csv"),
    ("eng/info_pages.txt", "aioutput/info_pages.csv"),
    ("eng/item_kinds1.txt", "aioutput/item_kinds.csv"),
    ("eng/menus.txt", "aioutput/game_menus.csv"),
    ("eng/parties.txt", "aioutput/parties.csv"),
    ("eng/party_templates.txt", "aioutput/party_templates.csv"),
    ("eng/quests.txt", "aioutput/quests.csv"),
    ("eng/quick_strings.txt", "aioutput/quick_strings.csv"),
    ("eng/skills.txt", "aioutput/skills.csv"),
    ("eng/strings.txt", "aioutput/game_strings.csv"),
    ("eng/troops.txt", "aioutput/troops.csv"),
]

# 术语表
with open(GLOSSARY_FILE, "r", encoding="utf-8") as f:
    GLOSSARY = json.load(f)
CURRET_SYS_PROMPT = sys_prompt.site_system_prompt(GLOSSARY)

# 翻译风格
STYLE_GUIDE = "formal and concise"

# === 2. 初始化客户端 & 缓存 ===
client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)
else:
    cache = {}


# === 3. 翻译函数（带缓存） ===
async def translate_text(text: str):
    # 如果已有缓存，直接返回
    if text in cache:
        return cache[text]

    system_prompt = CURRET_SYS_PROMPT
    response = await client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {"role": "user", "content": f"Source text:\n{text.replace('_',' ')}"},
        ],
        temperature=0,
    )

    content = response.choices[0].message.content
    translated = content.strip() if content is not None else ""
    cache[text] = translated
    return translated


# === 批量处理 ===
async def process_batch(pairs):
    tasks = [translate_text(text) for key, text in pairs]
    results = await asyncio.gather(*tasks)
    return [(_id, translated) for (_id, _), translated in zip(pairs, results)]


async def main():
    text_dict: dict[str, str] = {}
    translation: dict = {}
    # 从文件读取（你也可以改成直接传字符串）
    not_info_line = False
    with open(SOURCE_FILE, "r", encoding="utf-8") as f:
        source_pairs = []
        for line in f:
            if not_info_line:
                not_info_line = False
                continue

            [_, _, _, _, key, text, _] = line.split(" ", 6)
            not_info_line = True
            if text.strip():
                source_pairs.append((key, text.strip()))
    # 翻译
    results = []
    for i in range(0, len(source_pairs), BATCH_SIZE):
        batch = source_pairs[i : i + BATCH_SIZE]
        print(f"Processing lines {i+1} - {i+len(batch)}")
        translated_batch = await process_batch(batch)
        results.extend(translated_batch)
        # 保存缓存
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False, indent=2)

        # 追加保存翻译结果（保留ID）
        async with aiofiles.open(RESULT_FILE, "a", encoding="utf-8") as f:
            for _id, text in translated_batch:
                await f.write(f"{_id}|{text}\n")


# === 4. 示例使用 ===
if __name__ == "__main__":
    asyncio.run(main())
