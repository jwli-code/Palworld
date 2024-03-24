# 遍历所有拆分后的文件
wk=$PWD
for part_file in "${wk}"/list_part_*; do
    # 使用nohup和&在后台运行你的脚本，针对每个拆分文件
    nohup pipeline.sh $part_file > ${part_file}_log.txt 2>&1 &
done
