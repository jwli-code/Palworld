#!/bin/bash

# 定义工作路径
wk=$PWD
list_file="${wk}/list.txt"

# 计算每个文件应有的行数（向上取整）
total_lines=$(wc -l < "${list_file}")
((lines_per_file = (total_lines + 9) / 17))

# 使用split命令拆分文件
split -l ${lines_per_file} "${list_file}" "${wk}/list_part_"

