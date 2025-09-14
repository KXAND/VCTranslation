# 由 chatgpt生成
import asyncio
import json
import os
import re
import time
from openai import AsyncOpenAI
import aiofiles
import sys_prompt
from key import _API_KEY

# === 1. 配置 ===
API_KEY = _API_KEY
BASE_URL = "https://api.siliconflow.cn/v1"
BATCH_SIZE = 10  # 每批处理的 Unit 个数
BATCH_UNIT = 20  # 每次请求包含的行数

# 翻译
TRANSLATE_MODEL = "moonshotai/Kimi-K2-Instruct"  # 翻译模型名
SOURCE_DIR = "comparation/"
CACHE_FILE = "translation_cache.json"  # 缓存文件
GLOSSARY_FILE = "GLOSSARY.json"  # 术语文件
TARGET_FILES = [
    "dialogs",
    "game_menus",
    "game_strings",
    "info_pages",
    "quests",
    "quick_strings",
    "skills",
]  # 无扩展名

# 校对
ENABLE_PROOFREAD = False  # 启用校对
PROOFREAD_MODEL = "Qwen/Qwen3-8B"  # 校验模型名
CACHE_PRF_FILE = "proofread_cache.json"  # 校对缓存文件
ERROR_LOG_FILE = "errorlog.json"
ERROR_LOG = []


# 载入术语表，并将Troops和Fractions
def get_global_GLOSSAARY():
    with open(GLOSSARY_FILE, "r", encoding="utf-8") as f:
        glossary = json.load(f)
    for file in ["troops", "factions", "parties"]:
        with open("comparation\\" + file + ".json", "r", encoding="utf-8") as f:
            data = json.load(f)
        for _, eng, *_, translation in data:
            eng: str
            eng = eng.replace("_", " ")
            if glossary.get(eng) is None:
                glossary[eng] = translation
    return glossary


GLOSSARY: dict = get_global_GLOSSAARY()


CURRET_SYS_PROMPT = sys_prompt.sentence_system_prompt
CURRET_PROOFREAD_SYS_PROMPT = sys_prompt.sentence_proofread_prompt

CONTENT_DESCRIPTION = {
    "dialogs": "对话文本",
    "game_menus": "菜单显示文本",
    "game_strings": "对话文本",
    "hints": "提示文本",
    "info_pages": "百科文本",
    "skills": "技能文本",
    "quests": "任务信息",
    "quick_strings": "对话文本",
    # 词汇
    "party_templates": "地名和组织名",
    "parties": "地点名称",
    "factions": "阵营名称",
    "item_kinds": "物品名称",
    "troops": "人名或身份名",
    # 不翻译
    "skins": "皮肤描述词",
    "item_modifiers": "物品修饰词",
    "ui": "UI信息",
    "uimain": "UI信息",
}

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
    def build_glossary_pattern(glossary):
        # 按长度排序，长的优先，避免 "AI" 先匹配了 "Artificial Intelligence"
        terms = sorted(glossary.keys(), key=len, reverse=True)
        escaped = [re.escape(term) for term in terms]
        pattern = re.compile(r"\b(?:" + "|".join(escaped) + r")\b", flags=re.IGNORECASE)
        return pattern

    glossary = {}
    pattern = build_glossary_pattern(GLOSSARY)
    keys = set(GLOSSARY.keys())

    for key, text, reference, *_ in text_bundle:
        for match in pattern.findall(text.replace("_", " ")):
            term = next(k for k in GLOSSARY if k.lower() == match.lower())
            glossary[term] = GLOSSARY[term]
    return glossary


# === 3. 翻译函数（带缓存） ===
async def translate_text(
    text_bundle,
    system_prompt,
    model,
    cache,
    use_reference_trans=True,
):
    user_prompt = ""
    cnt_sent = 0
    # 剔除已经在缓存中的结果
    for key, text, reference, *_ in text_bundle:
        cleaned_text = text.replace("_", " ").strip()
        if cleaned_text not in cache and cleaned_text != "":
            user_prompt += cleaned_text
            if use_reference_trans == True:
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
            return await translate_text(text_bundle, system_prompt, model, cache)

        # 错误情况：结果数量不匹配
        translation_pairs = content.replace("\n\n", "\n").strip().split("\n")
        if len(translation_pairs) != cnt_sent:
            print(
                f"翻译数目不匹配。输入： {len(translation_pairs)}   {len(text_bundle)}  {cnt_sent}"
            )
            print(translation_pairs)
            print(text_bundle)
            if use_reference_trans == False:
                ERROR_LOG.append(
                    {"input": str(text_bundle), "output": str(translation_pairs)}
                )
                return {}
            return await translate_text(
                text_bundle,
                system_prompt,
                model,
                cache,
                use_reference_trans=False,
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


async def process_unit(unit, content_section, glossary):
    unit_start = time.time()
    start = time.time()

    translated = await translate_text(
        unit,
        CURRET_SYS_PROMPT(content_section, glossary),
        TRANSLATE_MODEL,
        translation_cache,
    )
    total_time = time.time() - start
    print(f"    translate_text completed in {total_time:.2f}s")

    proofreaded = translated
    if ENABLE_PROOFREAD:
        start = time.time()
        proofreaded = await translate_text(
            translated,
            CURRET_PROOFREAD_SYS_PROMPT(glossary),
            PROOFREAD_MODEL,
            proofread_cache,
        )
        total_time = time.time() - start
        print(f"     proofread completed in {total_time:.2f}s")

    unit_total_time = time.time() - unit_start
    print(f"    process_unit completed in {unit_total_time:.2f}s")
    return proofreaded


# === 批量处理 ===
async def process_batch(batch, content_section):
    units = [batch[i : i + BATCH_UNIT] for i in range(0, len(batch), BATCH_UNIT)]
    tasks = [
        process_unit(unit, content_section, get_local_glossary(unit)) for unit in units
    ]

    # gather 是原始序列的顺序
    results = await asyncio.gather(*tasks)
    returns = []
    for unit, translated_unit in zip(units, results):
        for (key, text, reference, *_), (_, _, translated) in zip(
            unit, translated_unit
        ):
            returns.append((key, text, reference, translated))
    return returns


def get_added_space_text(text: str):
    return re.sub(r"([\u4e00-\u9fa5。；，：“”（）、？《》！·…—])", r"\1 ", str(text))


async def main():
    for target_file in TARGET_FILES:
        print(f"Processing {target_file}...")
        # 从文件读取
        with open(SOURCE_DIR + target_file + ".json", "r", encoding="utf-8") as f:
            source_pairs = json.load(f)

        # 翻译
        results = []
        for i in range(0, len(source_pairs), BATCH_SIZE * BATCH_UNIT):
            batch = source_pairs[i : i + BATCH_SIZE * BATCH_UNIT]
            print(f"  Processing lines {i+1} - {i+len(batch)}")
            translated_batch = await process_batch(
                batch, CONTENT_DESCRIPTION.get(target_file, "内容")
            )
            results.extend(translated_batch)

            # 写入缓存
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(translation_cache, f, ensure_ascii=False, indent=2)
            with open(CACHE_PRF_FILE, "w", encoding="utf-8") as f:
                json.dump(proofread_cache, f, ensure_ascii=False, indent=2)

        # 输出对比文件，与前一版本对比
        async with aiofiles.open(
            SOURCE_DIR + target_file + "" + ".json", "w", encoding="utf-8"
        ) as f:
            json_content = json.dumps(results, ensure_ascii=False, indent=2)
            await f.write(json_content)

        print(f"{target_file} is done")
    with open(ERROR_LOG_FILE, "w", encoding="utf-8") as f:
        json.dump(ERROR_LOG, f, ensure_ascii=False, indent=2)


# === 4. 示例使用 ===
if __name__ == "__main__":
    asyncio.run(main())
