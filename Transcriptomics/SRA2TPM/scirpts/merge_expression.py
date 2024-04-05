import pandas as pd
import os
import sys

# 检查命令行参数是否正确
if len(sys.argv) != 3:
    print("Usage: python merge_files.py input_file_list output_file")
    sys.exit(1)

input_file_list = sys.argv[1]
output_file = sys.argv[2]

# 读取文件列表
with open(input_file_list, "r") as file:
    file_list = file.read().splitlines()

# 初始化一个空的DataFrame用于合并所有数据
merged_data = pd.DataFrame()

for file_name in file_list:
    # 生成完整的文件名
    full_file_name = file_name + ".tab"

    # 读取文件
    data = pd.read_csv(full_file_name, sep="\t", usecols=["Gene ID", "TPM"])

    # 提取列名
    column_name = os.path.splitext(os.path.basename(full_file_name))[0]

    # 重命名TPM列为列名
    data.rename(columns={"TPM": column_name}, inplace=True)

    # 如果是第一个文件，直接赋值给merged_data
    if merged_data.empty:
        merged_data = data
    else:
        # 否则，根据"Gene ID"合并数据
        merged_data = pd.merge(merged_data, data, on="Gene ID", how="outer")

# 保存合并后的数据到输出文件
merged_data.to_csv(output_file, index=False, sep="\t")
