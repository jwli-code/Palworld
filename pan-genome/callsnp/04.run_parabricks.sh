spec=JZS.v2
nt=10
wk=/public/home/yclin/jwli/data1/Bol_callsnp
workplace=$wk/${spec}
ref=$workplace/00ref/${spec}.genome.fa
bam_file=${workplace}/05.FinalBam
#chr_list=$(echo $(echo C{01..09}))
#if [ ! -d ${workplace}/log_gvcf ];then mkdir -p ${workplace}/log_gvcf;fi
#if [ ! -d ${workplace}/03.OriGVCF ];then mkdir -p ${workplace}/03.OriGVCF;fi
#${workplace}/03.OriGVCF

#cat /public/home/yclin/jwli/data1/Bol_callsnp/script/sra3.list|while read id;
ls ${bam_file}/*.sorted.markdup.bam |while read id;
do
i=`basename $id .sorted.markdup.bam`
#i=`basename $id`
bsub -J ${i}_parabricks -n $nt -R span[hosts=1] -gpu "num=1:gmem=12G" -o ${workplace}/log_gvcf/${i}.out -e ${workplace}/log_gvcf/${i}.err -q gpu  \
"sh parabricks_v1.sh $i $spec  $workplace $ref"
done
