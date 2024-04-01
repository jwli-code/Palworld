#!/bin/bash
# Description:
# This script merges the 10th column of multiple VCF files into a single file.
# It assumes that the first 9 columns of all VCF files are identical.
# The script takes three arguments:
# 1. The directory containing the VCF files.
# 2. A file listing all sample names to be processed.
# 3. The output file path for the merged VCF data.

# 检查参数数量
if [ "$#" -ne 3 ]; then
    echo "Usage: $0 <vcf_directory> <sample_file> <output_file>"
    exit 1
fi

# 使用命令行参数
vcf_directory=$1
sample_file=$2
output_file=$3

# 创建临时目录存放中间文件
temp_dir=$(mktemp -d)

# 从第一个文件中提取头部信息和前9列
first_sample=$(head -n 1 "$sample_file")
grep '^##' "$vcf_directory/${first_sample}_genotyping_biallelic_sv.vcf" > "$temp_dir/header.vcf"

# 提取第一个文件的前9列（非注释行）
grep -v '^##' "$vcf_directory/${first_sample}_genotyping_biallelic_sv.vcf" | cut -f1-9 > "$temp_dir/cols1-9.vcf"

# 提取每个样本文件的第10列
while IFS= read -r sample; do
    grep -v '^##' "$vcf_directory/${sample}_genotyping_biallelic_sv.vcf" | cut -f10 > "$temp_dir/${sample}_col10.vcf"
done < "$sample_file"

# 合并所有第10列
paste "$temp_dir"/*_col10.vcf > "$temp_dir/all_samples_col10.vcf"

# 合并头部、前9列和所有第10列到最终的输出文件
cat "$temp_dir/header.vcf" > "$output_file"
paste "$temp_dir/cols1-9.vcf" "$temp_dir/all_samples_col10.vcf" >> "$output_file"

# 清理临时文件
rm -rf "$temp_dir"

echo "合并完成，输出文件为 $output_file"
