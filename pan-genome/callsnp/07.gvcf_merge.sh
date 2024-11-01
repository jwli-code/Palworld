module load Singularity/3.7.3
module load GATK/4.5.0.0
module load HTSlib/1.9
module load SAMtools/1.9
module load BCFtools/1.8
i=$1
ref=$2
TH1=$3
chr_list=$(echo $(echo C{01..09}) other) #优化
for th in ${TH1};do
        for chr in ${chr_list};do

                bgzip -f ${th}/${i}_${chr}.gvcf && rm ${th}/${i}_${chr}.gvcf.idx

                singularity exec --nv  $IMAGE/clara-parabricks/4.0.1-1.sif pbrun indexgvcf --input ${th}/${i}_${chr}.gvcf.gz

        done
done

for th in ${TH1};do

        gatk CombineGVCFs -R ${ref} $(ls ${th}/${i}_*.gvcf.gz|xargs -i echo "--variant {}") -O ${th}/${i}.gvcf.gz

        singularity exec --nv  $IMAGE/clara-parabricks/4.0.1-1.sif pbrun indexgvcf --input ${th}/${i}.gvcf.gz

done
