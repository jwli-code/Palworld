#!/bin/bash
# @Author: jwli.
# @Date  : 2024/04/16
# 设置时间戳，用于文件命名
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# 创建以当前时间戳命名的新目录
mkdir -p "$TIMESTAMP"
cd "$TIMESTAMP"

# 下载文件
wget -O pubmed.html "https://pubmed.ncbi.nlm.nih.gov/?term=%28%28Brassica+napus%29+OR+%28B.napus%29%29+OR+%28oilseed+rape%29&filter=datesearch.y_1&sort=pubdate&format=pubmed&size=200"

# 提取HTML内容
python ../read.html.py pubmed.html > pubmed.txt

# 提取有用信息
python ../extract_pubmed_info.py pubmed.txt pubmed_info.xlsx

# 过滤出新的文献信息
python ../diff_pubmed_info.py pubmed_info.xlsx ../doi.test add_pubmed_info.xlsx

# 更新DOI列表，合并新旧DOI
python ../merge_doi_lists.py ../doi.test pubmed_info.xlsx updated_doi.test
cp updated_doi.test ../doi.test  # 更新全局DOI列表

# 返回上级目录
cd ..
