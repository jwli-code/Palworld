micromamba activate gemoma
#1.从转录组比对文件提取intron（没有也没关系，只是帮助后面的步骤，提高精度）
java -jar /home/jwli/miniconda3/share/gemoma-1.9-0/GeMoMa-1.9.jar CLI ERE m=merge.bam  outdir=./01_ERE_intron
#2.各亲缘物种提取CDS、比对目标基因组、进行注释（看物种基因组大小，一般3h左右）
mmseqs createdb Brassica_napus.ZS11.v0.genome.fa TargetGenomeDB
mmseqs createindex TargetGenomeDB tmp
#
