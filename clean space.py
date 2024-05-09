import os
import pandas as pd
import re
import io

input_path = 'cns/'
work_path = 'work_cns/'


def remove_space_after_chinese(cell):
    # 在所有的汉字后面删去空格，但是忽略"__NULL__"
    if cell != '__NULL__':
        return re.sub(r'([\u4e00-\u9fa5。；，：“”（）、？《》！^·…—0123456789])\s', r'\1', str(cell))
    else:
        return cell

for filename in os.listdir(input_path):
    if filename.endswith(".csv"):
        with open(os.path.join(input_path, filename), 'r', encoding='utf-8') as f:
            data = f.read()

        # 替换所有的"||"为"__NULL__"
        data = data.replace('||', '|__NULL__')
        
        # 用pandas读取处理过的字符串
        df = pd.read_csv(io.StringIO(data), sep='|', dtype=str, header=None)

        df = df.applymap(remove_space_after_chinese)

        # # 把"__NULL__"替换回"||"
        # df.replace('__NULL__', '|',regex=True,inplace=True)
        
        data_str = df.to_csv(sep='|', index=False, header=None)

        # 然后在字符串上进行替换操作
        data_str = data_str.replace('__NULL__', '|')

        # 最后，将替换后的字符串写入文件
        with open(os.path.join(work_path, filename), 'w',encoding='utf-8-sig',newline='\n') as f:
            f.write(data_str)
