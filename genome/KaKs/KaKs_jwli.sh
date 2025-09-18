#!/bin/bash
# Author: jwli
# Institution: HZAU
# Date: 2025.9.18

# 使用source加载conda环境
source /home/lchen/miniforge3/bin/activate /home/lchen/miniforge3/envs/kaks

[ $# -ne 6 ] && {
    echo "Usage: $0 genepair.list sample1.cds sample2.cds sample1.pep sample2.pep output_dir"
    exit 1
}

# 输入参数
GENEPAIR_LIST=$1
SAMPLE1_CDS=$2
SAMPLE2_CDS=$3
SAMPLE1_PEP=$4
SAMPLE2_PEP=$5
OUTPUT_DIR=$6

# 软件路径
KAKS_CALC="/home/lchen/biotool/KaKs_Calculator-3.0/bin/KaKs"
TRIMAL="trimal"
GBLOCKS="Gblocks"

# 检查软件
command -v muscle >/dev/null || { echo "muscle not found"; exit 1; }
command -v pal2nal.pl >/dev/null || { echo "pal2nal.pl not found"; exit 1; }
command -v "$TRIMAL" >/dev/null || { echo "TrimAl not found"; exit 1; }
command -v "$GBLOCKS" >/dev/null || { echo "Gblocks not found"; exit 1; }
[ -f "$KAKS_CALC" ] || { echo "KaKs_Calculator not found"; exit 1; }

# 检查输入文件
for f in "$GENEPAIR_LIST" "$SAMPLE1_CDS" "$SAMPLE2_CDS" "$SAMPLE1_PEP" "$SAMPLE2_PEP"; do
    [ -f "$f" ] || { echo "File $f not found"; exit 1; }
done

mkdir -p "$OUTPUT_DIR"

# 初始化汇总表格文件
SUMMARY_FILE="${OUTPUT_DIR}/kaks_summary.csv"
echo "Gene1,Gene2,Ka,Ks,Ka/Ks,Status" > "$SUMMARY_FILE"

# 初始化合并的kaks结果文件
KAKS_RESULTS="${OUTPUT_DIR}/all_kaks_results.txt"
> "$KAKS_RESULTS"

cleanup() {
    local prefix=$1
    rm -f "${prefix}".{pep,cds,aln,cds.aln,cds.aln.trim,cds.aln.gb,axt,kaks}
}

run_kaks() {
    local axt_file=$1
    local out_file=$2
    local gene1=$3
    local gene2=$4

    "$KAKS_CALC" -i "$axt_file" -o "$out_file" -m YN

    # 检查KaKs结果是否有效
    if [ -s "$out_file" ] && awk 'NR==2 && $3 != "NA" && $4 != "NA"' "$out_file" | grep -q .; then
        return 0  # 成功
    else
        return 1  # 失败
    fi
}

process_pair() {
    local gene1=$1 gene2=$2
    local cds1=$3 cds2=$4 pep1=$5 pep2=$6
    local outdir=$7
    local tmp_dir="$outdir/tmp"

    mkdir -p "$tmp_dir"
    local prefix="$tmp_dir/${gene1}_${gene2}"

    # 提取序列
    local p1=$(awk -v id="$gene1" -v RS=">" '$1==id {print ">"$0}' "$pep1")
    local p2=$(awk -v id="$gene2" -v RS=">" '$1==id {print ">"$0}' "$pep2")
    local c1=$(awk -v id="$gene1" -v RS=">" '$1==id {print ">"$0}' "$cds1")
    local c2=$(awk -v id="$gene2" -v RS=">" '$1==id {print ">"$0}' "$cds2")

    [ -z "$p1" ] || [ -z "$p2" ] || [ -z "$c1" ] || [ -z "$c2" ] && {
        echo -e "$gene1\t$gene2\tNA\tNA\tNA\tMissing sequence" | tee -a "${OUTPUT_DIR}/kaks_results.txt"
        echo "$gene1,$gene2,NA,NA,NA,Missing sequence" >> "$SUMMARY_FILE"
        return
    }

    echo -e "$p1\n$p2" > "${prefix}.pep"
    echo -e "$c1\n$c2" > "${prefix}.cds"

    # MUSCLE比对
    muscle -align "${prefix}.pep" -output "${prefix}.aln" -threads 2 || {
        echo -e "$gene1\t$gene2\tNA\tNA\tNA\tMUSCLE failed" | tee -a "${OUTPUT_DIR}/kaks_results.txt"
        echo "$gene1,$gene2,NA,NA,NA,MUSCLE failed" >> "$SUMMARY_FILE"
        return
    }

    # PAL2NAL转换
    pal2nal.pl "${prefix}.aln" "${prefix}.cds" -output fasta > "${prefix}.cds.aln" || {
        echo -e "$gene1\t$gene2\tNA\tNA\tNA\tPAL2NAL failed" | tee -a "${OUTPUT_DIR}/kaks_results.txt"
        echo "$gene1,$gene2,NA,NA,NA,PAL2NAL failed" >> "$SUMMARY_FILE"
        return
    }

    # 尝试1: TrimAl处理
    "$TRIMAL" -in "${prefix}.cds.aln" -out "${prefix}.cds.aln.trim" -automated1 || {
        echo -e "$gene1\t$gene2\tNA\tNA\tNA\tTrimAl failed" | tee -a "${OUTPUT_DIR}/kaks_results.txt"
        echo "$gene1,$gene2,NA,NA,NA,TrimAl failed" >> "$SUMMARY_FILE"
        return
    }

    # 转换为AXT格式
    echo "${gene1}_${gene2}" > "${prefix}.axt"
    grep -v "^>" "${prefix}.cds.aln.trim" | grep -v "^$" | grep -v "^-*$" >> "${prefix}.axt"

    # 第一次KaKs计算
    local out="${prefix}.kaks"
    local status="Success"
    local method="TrimAl"

    if ! run_kaks "${prefix}.axt" "$out" "$gene1" "$gene2"; then
        # 第一次计算失败，尝试使用Gblocks

        # 运行Gblocks但不检查其返回值
        "$GBLOCKS" "${prefix}.cds.aln" -t=c -b4=5 -b5=h -e=.gb

        # 检查Gblocks是否生成了输出文件
        if [ ! -f "${prefix}.cds.aln.gb" ]; then
            echo -e "$gene1\t$gene2\tNA\tNA\tNA\tGblocks output missing" | tee -a "${OUTPUT_DIR}/kaks_results.txt"
            echo "$gene1,$gene2,NA,NA,NA,Gblocks output missing" >> "$SUMMARY_FILE"
            return
        fi

        # 使用Gblocks结果生成新的AXT文件
        echo "${gene1}_${gene2}" > "${prefix}.axt"
        grep -v "^>" "${prefix}.cds.aln.gb" | grep -v "^$" | grep -v "^-*$" >> "${prefix}.axt"

        # 第二次KaKs计算
        method="Gblocks"
        if ! run_kaks "${prefix}.axt" "$out" "$gene1" "$gene2"; then
            status="KaKs calculation failed after both methods"
            echo -e "$gene1\t$gene2\tNA\tNA\tNA\t$status" | tee -a "${OUTPUT_DIR}/kaks_results.txt"
            echo "$gene1,$gene2,NA,NA,NA,$status" >> "$SUMMARY_FILE"
            return
        else
            status="Success after Gblocks"
        fi
    fi

    # 处理kaks结果文件
    if [ ! -s "$KAKS_RESULTS" ]; then
        # 第一次写入，包含标题
        cat "$out" > "$KAKS_RESULTS"
    else
        # 后续写入，跳过标题
        awk 'NR>1' "$out" >> "$KAKS_RESULTS"
    fi

    local result=$(awk 'NR==2 {print $3"\t"$4"\t"$5}' "$out")
    echo -e "$gene1\t$gene2\t${result}\t$method $status" | tee -a "${OUTPUT_DIR}/kaks_results.txt"
    echo "$gene1,$gene2,$(echo $result | tr '\t' ','),$method $status" >> "$SUMMARY_FILE"

    cleanup "$prefix"
}

# 清空或创建结果文件
> "${OUTPUT_DIR}/kaks_results.txt"

# 主循环
while IFS=$'\t' read -r g1 g2; do
    [[ "$g1" =~ ^# ]] || [[ -z "$g1" || -z "$g2" ]] && continue
    process_pair "$g1" "$g2" "$SAMPLE1_CDS" "$SAMPLE2_CDS" "$SAMPLE1_PEP" "$SAMPLE2_PEP" "$OUTPUT_DIR"
done < "$GENEPAIR_LIST"

echo "Done. Results in:"
echo " - Detailed results: ${OUTPUT_DIR}/kaks_results.txt"
echo " - Summary table: ${SUMMARY_FILE}"
echo " - All KAKS results: ${KAKS_RESULTS}"
