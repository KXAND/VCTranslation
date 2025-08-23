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
TRANSLATE_MODEL = "moonshotai/Kimi-K2-Instruct"  # 模型名
PROOFREAD_MODEL = "Qwen/Qwen3-8B"  # 模型名
SOURCE_DIR = "comparation/"
RESULT_DIR = "Qwen2.5-72B-Instruct-128K/"
CACHE_FILE = "translation_cache.json"  # 缓存文件
CACHE_PRF_FILE = "proofread_cache.json"  # 校对缓存文件
GLOSSARY_FILE = "GLOSSARY.json"  # 缓存文件
SOURCE_LANGUAGE = "English"
TARGET_LANGUAGE = "Chinese"
TARGET_FILES = ["quick_strings"]  # without extension name
BATCH_SIZE = 10  # 每批处理的 Unit 个数
BATCH_UNIT = 20  # 每次请求包含的行数

# 术语表
with open(GLOSSARY_FILE, "r", encoding="utf-8") as f:
    GLOSSARY = json.load(f)
CURRET_SYS_PROMPT = sys_prompt.sentence_system_prompt
CURRET_PROOFREAD_SYS_PROMPT = sys_prompt.sentence_proofread_prompt
# 翻译风格
STYLE_GUIDE = "formal and concise"

# === 2. 初始化客户端 & 缓存 ===
client = AsyncOpenAI(api_key=API_KEY, base_url=BASE_URL)
if os.path.exists(CACHE_FILE):
    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        translation_cache = json.load(f)
else:
    translation_cache = {}

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
async def translate_text(text_bundle, system_prompt, model, cache, glossary=GLOSSARY):
    user_prompt = ""
    cnt_sent = 0
    # 剔除已经在缓存中的结果
    for key, text, reference, *_ in text_bundle:
        cleaned_text = text.replace("_", " ").strip()
        if cleaned_text not in cache and cleaned_text != "":
            user_prompt += cleaned_text
            user_prompt += ("，参考翻译: " + reference) if reference else ""
            user_prompt += "\n"
            cnt_sent += 1

    # 如果并非都在缓存中，调用AI翻译并写入到 cache 中
    translated = []
    if user_prompt.strip() != "":
        # 获取结果

        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"\n{user_prompt}",
                },
            ],
            temperature=0,
            # extra_body={"enable_thinking": False},
        )

        # 错误情况：结果为空
        content = response.choices[0].message.content
        if content is None:
            return await translate_text(
                text_bundle, system_prompt, model, cache, glossary
            )

        # 错误情况：结果数量不匹配
        translation_pairs = content.replace("\n\n", "\n").strip().split("\n")
        if len(translation_pairs) != cnt_sent:
            print(
                f"翻译数目不匹配。输入： {len(translation_pairs)}   {len(text_bundle)}  {cnt_sent}"
            )
            print(translation_pairs)
            print(text_bundle)
            return await translate_text(
                text_bundle, system_prompt, model, cache, glossary
            )

        # 新翻译塞入 cache
        i = 0
        for key, text, _ in text_bundle:
            cleaned_text = text.replace("_", " ").strip()
            if cleaned_text in cache or cleaned_text == "":
                continue
            try:
                trans = translation_pairs[i]
                cache[cleaned_text] = trans
                i += 1
            except:
                i += 1
                print(
                    f"已忽略不正确的返回格式对，内容为：{ trans} i={i} cleaned_text={cleaned_text}"
                )

    # 从 cache 中取出所有的翻译
    for key, text, reference, *_ in text_bundle:
        cleaned_text = text.replace("_", " ").strip()
        translated.append([key, text, cache.get(cleaned_text)])
    return translated


async def process_unit(unit):
    unit_start = time.time()
    glossary = get_local_glossary(unit)

    start = time.time()
    translated = await translate_text(
        unit,
        CURRET_SYS_PROMPT(glossary),
        TRANSLATE_MODEL,
        translation_cache,
        glossary,
    )
    total_time = time.time() - start
    print(f"translate_text completed in {total_time:.2f}s")

    proofreaded = translated
    # start = time.time()
    # proofreaded = await translate_text(
    #     translated,
    #     CURRET_PROOFREAD_SYS_PROMPT(glossary),
    #     PROOFREAD_MODEL,
    #     proofread_cache,
    #     glossary,
    # )
    # total_time = time.time() - start
    # print(f"translate_text completed in {total_time:.2f}s")

    unit_total_time = time.time() - unit_start
    print(f"process_unit completed in {unit_total_time:.2f}s")
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
                json.dump(translation_cache, f, ensure_ascii=False, indent=2)
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
