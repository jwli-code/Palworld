
# merge_doi_lists.py
import sys

old_doi_file = sys.argv[1]
new_data_file = sys.argv[2]
output_file = sys.argv[3]

# 读取旧的DOI列表
with open(old_doi_file, 'r') as file:
    old_dois = set(file.read().splitlines())

# 假设新的DOI存储在xlsx的第一列
import pandas as pd
data = pd.read_excel(new_data_file)
new_dois = set(data.iloc[:, 2].dropna().astype(str).tolist())  # 修改列号根据实际情况

# 合并DOI列表
updated_dois = old_dois.union(new_dois)

# 写入合并后的DOI列表
with open(output_file, 'w') as file:
    for doi in sorted(updated_dois):
        file.write(f"{doi}\n")
