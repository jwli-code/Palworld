#hisat2_single.sh
ref=$1
#ref为index的前缀
gtf=$2
fq1=$3
cpu=$4
s=$5

if [ ! -d 03.bams ];then mkdir 03.bams;fi
if [ ! -d 04.stringtie/${s} ];then mkdir -p 04.stringtie/${s};fi

(hisat2 -p $cpu --summary-file 03.bams/${s}_summary.txt --dta -x $ref -U $fq1 | samtools view -Sbho 03.bams/${s}.bam - 1>03.bams/${s}.log 2>03.bams/${s}.err ) 
samtools sort -@ $cpu -o 03.bams/${s}.srt.bam  03.bams/${s}.bam
samtools index 03.bams/${s}.srt.bam
stringtie 03.bams/${s}.srt.bam -p $cpu -G $gtf -e -B -o 04.stringtie/${s}/${s}.gtf -A 04.stringtie/${s}/${s}.tab -l ${s} 
rm 03.bams/${s}.srt.bam
rm 03.bams/${s}.bam
