import os
import pandas as pd
import re
import io


def add_space_after_chinese(cell):
    if cell == None:
        return cell
    return re.sub(r"([\u4e00-\u9fa5。；，：“”（）、？《》！·…—])", r"\1 ", str(cell))


def post_process(data, out_path):
    df = df.applymap(add_space_after_chinese)

    data_str = df.to_csv(sep="|", index=False, header=None)

    # 然后在字符串上进行替换操作
    data_str = data_str.replace("__NULL__", "|")

    # 最后，将替换后的字符串写入文件
    with open(
        os.path.join(out_path, filename), "w", encoding="utf-8-sig", newline="\n"
    ) as f:
        f.write(data_str)
