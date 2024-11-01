module load Singularity/3.7.3
module load GATK/4.5.0.0
module load HTSlib/1.9
module load SAMtools/1.9
module load BCFtools/1.8

i=$1
spec=$2
workplace=$3
ref=$4
#chr_list=$5
chr_list=$(echo $(echo C{01..09}) other)
#
for chr in ${chr_list};do
singularity exec --nv -B $workplace /share/Singularity/clara-parabricks/4.0.1-1.sif pbrun haplotypecaller \
 --interval-file ${workplace}/00ref/${spec}_${chr}.bed \
 --ref ${ref} \
 --tmp-dir ${workplace}/tmp \
 --in-bam ${workplace}/02.FinalBam/${i}.sorted.markdup.bam \
 --out-variants ${workplace}/03.OriGVCF/${i}_${chr}.gvcf --gvcf
done

