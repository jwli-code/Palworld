1.EDTA 运行
EDTA.pl --genome /public/home/jyxiao/jwli/NG_Bol/TE/genome/${line}.fasta --species others --anno 1 --step all --sensitive 1 --t 15

--sensitive  Use RepeatModeler to identify remaining TEs (1) or not (0, default). 时间较长
--step Specify which steps you want to run EDTA.
--anno 1
--force 1 会用水稻的库

genome.mod.EDTA.TElib.fa：最终结果，非冗余的TE库。如果在输入文件中用–curatedlib指定的修正版TE库，则该文件中也将包含这部分序列。
genome.mod.EDTA.TElib.novel.fa: 新TE类型。该文件包括在输入文件中用–curatedlib指定的修正版TE库没有的TE序列，即genome.mod.EDTA.TElib.fa减去–curatedlib指定库(需要–curatedlib参数)。
genome.mod.EDTA.TEanno.gff: 全基因组TE的注释。该文件包括结构完整和结构不完整的TE的注释（需要–anno 1参数）。
genome.mod.EDTA.TEanno.sum: 对全基因组TE注释的总结（需要–anno 1参数）。
genome.mod.MAKER.masked: 低阈值TE的屏蔽。该文件中仅包括长TE（>= 1 kb）序列(需要–anno 1参数)。
genome.mod.EDTA.TE.fa.stat.redun.sum: 简单TE的注释偏差(需要–evaluate 1参数)。
genome.mod.EDTA.TE.fa.stat.nested.sum：嵌套型TE注释的偏差（需要–evaluate 1参数）。
genome.mod.EDTA.TE.fa.stat.all.sum: 注释偏差的概述（需要–evaluate 1参数）。
