nt=18
spec=JZS.v2
wk=/public/home/yclin/jwli/data1/Bol_callsnp
workplace=$wk/${spec}
ref=$workplace/00ref/${spec}.genome.fa
cleandata=$workplace/00.cleandata
sra_dir=/public/home/lnzhang/data/Bnapus/Chiifu.v4/sra_00

if [ ! -d ${workplace}/00.cleandata ];then mkdir -p ${workplace}/00.cleandata;fi
if [ ! -d ${workplace}/log ];then mkdir -p ${workplace}/log;fi
if [ ! -d ${workplace}/log_fastp ];then mkdir -p ${workplace}/log_fastp;fi
if [ ! -d ${workplace}/tmp ];then mkdir -p ${workplace}/tmp;fi
if [ ! -d ${workplace}/03.OriGVCF ];then mkdir -p ${workplace}/03.OriGVCF;fi
if [ ! -d ${workplace}/00.Rawdata ];then mkdir -p ${workplace}/00.Rawdata ;fi
if [ ! -d ${workplace}/log_bwa ];then mkdir -p ${workplace}/log_bwa;fi
if [ ! -d ${workplace}/00.rawbam ];then mkdir -p ${workplace}/00.rawbam;fi
if [ ! -d ${workplace}/02.FinalBam ];then mkdir -p ${workplace}/02.FinalBam;fi
if [ ! -d ${workplace}/03.OriGVCF ];then mkdir -p ${workplace}/03.OriGVCF;fi

ls ${sra_dir} |while read id;do
#ls ${workplace}/sra7 |while read id;
#cat sra1.err |while read id;
#do
i=`basename $id`
#rm -rf ${workplace}/02.FinalBam/${i}.sorted.markdup.bam
#rm -rf ${workplace}/log/${i}.out
#rm -rf ${workplace}/log/${i}.err
#rm -rf ${clean_dir}/${i}.fq.gz
#rm -rf ${clean_dir}/${i}_1.fq.gz
#rm -rf ${clean_dir}/${i}_2.fq.gz
#rm -rf ${workplace}/00.rawbam/${i}.sorted.bam
#if [ ! -e ${clean_dir}/${i}.fq.gz ] && [ ! -e ${clean_dir}/${i}_1.fq.gz ] && [ ! -e ${workplace}/00.rawbam/${i}.sorted.bam ] && \
#   [ ! -e ${workplace}/02.FinalBam/${i}.sorted.markdup.bam ] && [ ! -e ${workplace}/03.OriGVCF/${i}_gvcf.gz ];then
   bsub -J ${i} -n $nt -R span[hosts=1] -o ${workplace}/log/${i}.out -e ${workplace}/log/${i}.err -q smp \
   "sh fastp2BWA_v3.sh  $i $nt ${workplace} ${workplace}/00.cleandata $ref ${sra_dir}"
#   fi
done


