# 由 chatgpt生成
import asyncio
import json
import os
import time
from openai import AsyncOpenAI
import aiofiles
import sys_prompt
from key import _API_KEY

# === 1. 配置 ===
API_KEY = _API_KEY
BASE_URL = "https://api.siliconflow.cn/v1"
TRANSLATE_MODEL_NAME = "Qwen/Qwen2.5-72B-Instruct-128K"  # 模型名
PROOFREAD_MODEL_NAME = "Qwen/Qwen3-8B"  # 模型名
SOURCE_DIR = "comparation/"
RESULT_DIR = "Qwen2.5-72B-Instruct-128K/"
CACHE_FILE = "translation_cache.json"  # 缓存文件
CACHE_PRF_FILE = "proofread_cache.json"  # 校对缓存文件
GLOSSARY_FILE = "GLOSSARY.json"  # 缓存文件
SOURCE_LANGUAGE = "English"
TARGET_LANGUAGE = "Chinese"
TARGET_FILES = ["troops", "party_templates"]  # without extension name
BATCH_SIZE = 10  # 每批处理的 Unit 个数
BATCH_UNIT = 20  # 每次请求包含的行数

# 术语表
with open(GLOSSARY_FILE, "r", encoding="utf-8") as f:
    GLOSSARY = json.load(f)
CURRET_SYS_PROMPT = sys_prompt.troop_system_prompt

# 翻译风格
STYLE_GUIDE = "formal and concise"

# === 2. 初始化客户端 & 缓存 ===
client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        cache = json.load(f)
else:
    cache = {}

if os.path.exists(CACHE_PRF_FILE):
    with open(CACHE_PRF_FILE, "r", encoding="utf-8") as f:
        proofread_cache = json.load(f)
else:
    proofread_cache = {}


def get_local_glossary(text_bundle):
    glossary = {}
    keys = set(GLOSSARY.keys())

    for key, text, reference, *_ in text_bundle:
        pieces = set(p.strip() for p in text.replace("_", " ").split() if p.strip())
        matched = pieces & keys
        for term in matched:
            glossary[term] = GLOSSARY[term]
    return glossary


# === 3. 翻译函数（带缓存） ===
async def translate_text(text_bundle, glossary=GLOSSARY):
    start = time.time()

    user_prompt = ""
    # 剔除已经在缓存中的结果
    for key, text, reference, *_ in text_bundle:
        refined_text = text.replace("_", " ")
        if refined_text not in cache:
            user_prompt += refined_text
            user_prompt += ("，参考译名: " + reference) if reference else ""
            user_prompt += "\n"

    translated = []
    if user_prompt.strip() == "":
        for key, text, reference, *_ in text_bundle:
            clean_text = text.replace("_", " ").strip()
            translated.append([key, text, cache.get(clean_text)])
        return translated

    system_prompt = CURRET_SYS_PROMPT(glossary)
    response = await client.chat.completions.create(
        model=TRANSLATE_MODEL_NAME,
        messages=[
            {"role": "system", "content": system_prompt.strip()},
            {
                "role": "user",
                "content": f"Source text:\n{user_prompt}",
            },
        ],
        temperature=0,
    )

    content = response.choices[0].message.content
    if content is not None:
        for translation_pair in content.strip().split("\n"):
            try:
                text, translation = translation_pair.strip().split(":")
                cache[text.strip()] = translation.strip()
            except:
                print("已忽略不正确的返回格式对，内容为：" + translation_pair)

    for key, text, reference, *_ in text_bundle:
        clean_text = text.replace("_", " ").strip()
        translated.append([key, text, cache.get(clean_text)])

    total_time = time.time() - start
    print(f"translate_text completed in {total_time:.2f}s")
    return translated


# === 4.单个请求的校对 ===
async def proofread_texts(text_bundle, glossary):
    start = time.time()

    user_prompt = ""
    # 剔除已经在缓存中的结果
    for key, text, translated in text_bundle:
        refined_text = text.replace("_", " ")
        if refined_text not in proofread_cache:
            user_prompt += refined_text
            user_prompt += ("，参考译名: " + translated) if translated else ""
            user_prompt += "\n"

    translateds = []
    if user_prompt.strip() == "":
        for key, text, translated in text_bundle:
            clean_text = text.replace("_", " ").strip()
            translateds.append([key, text, proofread_cache.get(clean_text)])
        return translateds

    resp = await client.chat.completions.create(
        model=PROOFREAD_MODEL_NAME,
        messages=[
            {"role": "system", "content": sys_prompt.proofread_prompt(glossary)},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0,
        extra_body={"enable_thinking": False},
    )
    checked_texts = resp.choices[0].message.content

    result = []
    if checked_texts is not None:
        for checked_text in checked_texts.strip().split("\n"):
            try:
                text, proofreaded_trans = checked_text.strip().split(":")
                proofread_cache[text.strip()] = proofreaded_trans.strip()
            except:
                print("已忽略不正确的返回格式对，内容为：" + checked_text)
    for key, text, translated in text_bundle:
        clean_text = text.replace("_", " ").strip()
        result.append([key, text, proofread_cache.get(clean_text)])

    total_time = time.time() - start
    print(f"proofread_texts completed in {total_time:.2f}s")
    return result


async def process_unit(unit):
    start = time.time()
    glossary = get_local_glossary(unit)
    translated = await translate_text(unit, glossary)
    proofreaded = await proofread_texts(translated, glossary)

    total_time = time.time() - start
    print(f"process_unit completed in {total_time:.2f}s")
    return proofreaded


# === 批量处理 ===
async def process_batch(batch):
    units = [batch[i : i + BATCH_UNIT] for i in range(0, len(batch), BATCH_UNIT)]

    tasks = [process_unit(unit) for unit in units]
    # gather 是原始序列的顺序，保证下面 glossary 顺序正确

    results = await asyncio.gather(*tasks)
    returns = []
    for unit, translated_unit in zip(units, results):
        for (key, text, reference, *_), (_, _, translated) in zip(
            unit, translated_unit
        ):
            returns.append((key, text, reference, translated))
    return returns


async def main():
    for target_file in TARGET_FILES:
        # 从文件读取（你也可以改成直接传字符串）
        with open(SOURCE_DIR + target_file + ".json", "r", encoding="utf-8") as f:
            source_pairs = json.load(f)

        # 翻译
        results = []
        for i in range(0, len(source_pairs), BATCH_SIZE * BATCH_UNIT):
            batch = source_pairs[i : i + BATCH_SIZE * BATCH_UNIT]
            print(f"Processing lines {i+1} - {i+len(batch)}")
            translated_batch = await process_batch(batch)
            results.extend(translated_batch)

            # 保存缓存
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(cache, f, ensure_ascii=False, indent=2)
            with open(CACHE_PRF_FILE, "w", encoding="utf-8") as f:
                json.dump(proofread_cache, f, ensure_ascii=False, indent=2)

            # 保存翻译结果为 csv
            async with aiofiles.open(
                RESULT_DIR + target_file + ".csv", "a", encoding="utf-8"
            ) as f:
                for key, _, _, text in translated_batch:
                    await f.write(f"{key}|{text}\n")
                    # 保存翻译结果为 csv

        async with aiofiles.open(
            RESULT_DIR + target_file + "_new" + ".json", "w", encoding="utf-8"
        ) as f:
            json_content = json.dumps(results, ensure_ascii=False, indent=2)
            await f.write(json_content)


# === 4. 示例使用 ===
if __name__ == "__main__":
    asyncio.run(main())
