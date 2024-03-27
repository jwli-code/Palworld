Description ：Gene extraction upstream and downstream
Use :  seqkit subseq --threads 5 -w 60 --up-stream 50000 --bed gene.bed -o up_50k.fasta genome.fasta



--only-flank   只提取侧翼序列，不包含bed的区间序列
--threads 线程数
-w 提取序列的单行宽度。0表示单行。
--up-stream 提取上游序列区间长度
--down-stream  提取下游序列区间长度
--bed 指定bed文件
-o  指定输出结果文件。当输出文件添加后缀.gz 时，即可得到压缩的输出结果文件。
命令接受输入文件为压缩格式。
