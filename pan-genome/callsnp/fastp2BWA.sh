#!/bin/bash

module load fastp/0.23.0
module load sratoolkit/2.9.6
#module load sratoolkit/3.0.7
module load pigz/2.3.4
module load SAMtools/1.9
module load BWA/0.7.17
module load picard/2.23.9

# 参数
i=$1
nt=$2
workplace=$3
clean_dir=$4
ref=$5
genome_name=`basename ${ref} .fa`

## sra2fastq

fasterq-dump -e $nt -3 ${workplace}/sra7/${i}/${i}.sra -O ${workplace}/00.Rawdata
#rm ${workplace}/01sra/${i}/${i}.sra
fq=${workplace}/00.Rawdata/${i}.sra.fastq
fq1=${workplace}/00.Rawdata/${i}.sra_1.fastq
fq2=${workplace}/00.Rawdata/${i}.sra_2.fastq

## cleandata
if [ -e $fq ]; then
    pigz -p $nt ${fq}
    fastp -i ${fq}.gz -o ${clean_dir}/${i}.fq.gz  -q 30 -j ${workplace}/log_fastp/${i}_.json -h ${workplace}/log_fastp/${i}.html && rm ${fq}.gz
else
    pigz -p $nt ${fq1}
    pigz -p $nt ${fq2}
    fastp -i ${fq1}.gz -I ${fq2}.gz -o ${clean_dir}/${i}_1.fq.gz -O ${clean_dir}/${i}_2.fq.gz -q 30 -j ${workplace}/log_fastp/${i}_.json -h ${workplace}/log_fastp/${i}.html && rm ${fq1}.gz ${fq2}.gz
fi

## bwa

if [ -e ${clean_dir}/${i}.fq.gz ]; then
    bwa mem -M -R "@RG\tID:${i}\tSM:${i}\tLB:WES\tPL:illumina" -t $nt $ref ${clean_dir}/${i}.fq.gz | samtools sort -@ $nt -o ${workplace}/00.rawbam/${i}.sorted.bam
    #rm -rf ${clean_dir}/${i}.fq.gz
else
        bwa mem -M -R "@RG\tID:${i}\tSM:${i}\tLB:WES\tPL:illumina" -t $nt $ref ${clean_dir}/${i}_1.fq.gz ${clean_dir}/${i}_2.fq.gz | samtools sort -@ $nt -o ${workplace}/00.rawbam/${i}.sorted.bam
    #rm -rf ${clean_dir}/${i}_1.fq.gz ${clean_dir}/${i}_2.fq.gz
fi

## Necessary :BUILD INDEX

#java -jar ${EBROOTPICARD}/picard.jar CreateSequenceDictionary R=${ref} O=/public/home/lnzhang/data/Bnapus/00ref/${genome_name}.dict

## MarkDuplicates
dedup_bam=${workplace}/02.FinalBam/${i}.sorted.markdup.bam
dedup_metrics=${workplace}/tmp/${i}.sorted.markdup_metrics.txt

java -jar ${EBROOTPICARD}/picard.jar MarkDuplicates \
    I=${workplace}/00.rawbam/${i}.sorted.bam \
    O=$dedup_bam \
    M=$dedup_metrics \
    CREATE_INDEX=True \
    REMOVE_DUPLICATES=True

stat=${workplace}/02.FinalBam/${i}.stat
stat1=${workplace}/02.FinalBam/${i}.stat1

samtools index -@ $nt ${workplace}/00.rawbam/${i}.sorted.bam
samtools index -@ $nt $dedup_bam
samtools flagstat -@ $nt $dedup_bam > $stat1
samtools flagstat -@ $nt ${workplace}/00.rawbam/${i}.sorted.bam > $stat
rm -rf ${workplace}/00.rawbam/${i}.sorted.bam ${workplace}/00.rawbam/${i}.sorted.bam.bai

# Optional: 转换为CRAM格式并删除BAM文件
#samtools view -C -T ${ref} $dedup_bam > ${workplace}/02.FinalBam/${i}.cram && rm $dedup_bam

