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
BATCH_UNIT = 25  # 每次请求包含的行数

# 翻译
TRANSLATE_MODEL = "moonshotai/Kimi-K2-Instruct"  # 翻译模型名
SOURCE_DIR = "comparation/"
CACHE_FILE = "translation_cache.json"  # 缓存文件
GLOSSARY_FILE = "GLOSSARY.json"  # 术语文件
TARGET_FILES = [
    "dialogs.1",
    "dialogs.2",
    "dialogs.3",
    "dialogs.4",
    "dialogs.5",
    "dialogs.6",
    "dialogs.7",
    "dialogs.8",
    "dialogs.9",
    "dialogs.10",
    "dialogs.11",
]  # 无扩展名
HUMAN_TRANSLATED_FILES = [
    "troops.0",
    "troops.1",
    "troops.2",
    "factions.0",
    "parties.0",
    # 已翻译
    "dialogs.0",
]  # 已有人类翻译的文件列表，无扩展名

# 校对
ENABLE_PROOFREAD = False  # 启用校对
PROOFREAD_MODEL = "Qwen/Qwen3-8B"  # 校验模型名
CACHE_PRF_FILE = "proofread_cache.json"  # 校对缓存文件
ERROR_LOG_FILE = "errorlog.json"
ERROR_LOG = []


# 载入术语表，并将Troops和Fractions视为Glossary
def get_global_GLOSSAARY():
    with open(GLOSSARY_FILE, "r", encoding="utf-8") as f:
        glossary = json.load(f)
    for file in HUMAN_TRANSLATED_FILES:
        with open("comparation\\" + file + ".json", "r", encoding="utf-8") as f:
            data = json.load(f)
        for eng, *_, translation in data:
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

    for entry in text_bundle:
        text = entry["text"].replace("_", " ")
        for match in pattern.findall(text):
            term = next(k for k in GLOSSARY if k.lower() == match.lower())
            glossary[term] = GLOSSARY[term]
    return glossary


# === 3. 翻译函数（带缓存） ===
async def translate_text(
    text_bundle,
    system_prompt,
    model,
    use_reference_trans=True,
    max_retries=3,
):
    payload = []
    for idx, item in enumerate(text_bundle):
        original_text = item.get("text", "").replace("_", " ").strip()
        reference = item.get("translation", "")

        entry = {"id": idx, "src": original_text}
        if use_reference_trans and reference:
            entry["ref"] = reference  # 作为参考翻译给出
        payload.append(entry)

    # 如果输入为空，直接返回
    if not payload:
        return []

    user_prompt = json.dumps(payload, ensure_ascii=False)
    for trying in range(max_retries):
        try:
            # 调用 AI 翻译
            response = await client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=0,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content
            if content is None:
                continue

            # 解析返回的 JSON
            try:
                # 清理markdown语法
                clean_content = re.sub(r"```json\s*|\s*```", "", content).strip()
                raw_data = json.loads(clean_content)

                # 数据返回格式：{result: [{id: 0, trans: "..."}, {}] }
                translated_list = []
                if isinstance(raw_data, list):  # case 1: 直接是列表
                    translated_list = raw_data
                elif isinstance(raw_data, dict):
                    translated_list = raw_data.get(
                        "result", []
                    )  # case 2: 返回标准格式，在dict 的 result字段
                    if not translated_list:
                        # 尝试寻找字典里的列表字段
                        for (
                            val
                        ) in raw_data.values():  # case 3: 返回 dict 但不是标准格式
                            if isinstance(val, list):
                                translated_list = val
                                break
            # 解析失败
            except json.JSONDecodeError:
                print(f"JSON 解析失败，正在重试... 返回内容: {content[:100]}")
                continue

            # 建立 ID 映射表 (ID -> 翻译结果)
            translated_data = {
                item["id"]: item.get("trans", "")
                for item in translated_list
                if "id" in item
            }

            # 错误情况：结果数量不匹配
            if len(translated_data) != len(payload):
                # print(
                #     f"翻译数目不匹配。预期: {len(payload)} 收到: {len(translated_data)}"
                # )
                # 如果重试多次失败，可以在此处增加降级逻辑（如拆分 batch）
                if trying == max_retries - 1:
                    ERROR_LOG.append({"input": user_prompt, "output": content})
                    return []
                continue

            # 匹配结果并返回与 text_bundle 一致的结构
            results = []
            for i, original_item in enumerate(text_bundle):
                results.append(
                    {
                        "text": original_item["text"],
                        "translation": translated_data.get(i, ""),
                    }
                )

            return results

        except Exception as e:
            print(f"请求发生异常: {e}")
            return []


# 翻译并校验一个单元
async def process_unit(unit, content_section, glossary):
    unit_start = time.time()
    start = time.time()

    translated = await translate_text(
        unit,
        CURRET_SYS_PROMPT(content_section, glossary),
        TRANSLATE_MODEL,
    )
    total_time = time.time() - start
    print(f"    translate_text completed in {total_time:.2f}s")

    # @todo：修改校对逻辑
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


# 并行翻译一个批次中的单元
async def process_batch(batch, content_section):
    units = [batch[i : i + BATCH_UNIT] for i in range(0, len(batch), BATCH_UNIT)]
    tasks = [
        process_unit(unit, content_section, get_local_glossary(unit)) for unit in units
    ]

    # gather 是原始序列的顺序
    results = await asyncio.gather(*tasks)
    returns = []
    for unit, translated_unit in zip(units, results):
        if not translated_unit:
            # 如果翻译失败返回了空列表，则保留原样（翻译设为空或保持旧版）
            for item in unit:
                returns.append(
                    {
                        "text": item.get("text"),
                        "old_translation": item.get("translation"),
                        "translation": "",  # 标记失败
                    }
                )
            continue

        # 进一步配对 unit 中的每一条数据与其翻译结果
        for original_item, new_item in zip(unit, translated_unit):
            returns.append(
                {
                    "text": original_item.get("text"),  # 原文
                    "old_translation": original_item.get(
                        "translation"
                    ),  # 这里的 trans 是输入的旧翻译
                    "translation": new_item.get(
                        "translation"
                    ),  # 这里的 trans 是 LLM 返回的新翻译
                }
            )

    return returns


async def main():
    # 如果没有值，则全量翻译（除已有人类翻译的文件），否则翻译指定文件
    if TARGET_FILES is None or len(TARGET_FILES) == 0:
        target_files = set(item.split(".")[0] for item in os.listdir(SOURCE_DIR)) - set(
            HUMAN_TRANSLATED_FILES
        )
    else:
        target_files = TARGET_FILES

    for target_file in target_files:
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
                batch, CONTENT_DESCRIPTION.get(target_file.split(".")[0], "内容")
            )
            results.extend(translated_batch)

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
