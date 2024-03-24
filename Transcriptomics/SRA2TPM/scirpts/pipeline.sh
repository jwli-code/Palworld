module load fastp/0.20.0
module load hisat2/2.2.0
module load StringTie/2.1.4
wk=$PWD
sample=$1
mkdir -p $wk/00.sra $wk/01.rawdata $wk/02.cleandata $wk/logs
sra_dir=$wk/00.sra
raw_dir=$wk/01.rawdata
clean_dir=$wk/02.cleandata
SINGLE_LIST=$wk/single.list
ref="/home/jwli/2024/Brassica/RNA-seq/Bra/pipeline/genome/Bra_Chiifu_v4.0"
gtf="/home/jwli/2024/Brassica/RNA-seq/Bra/pipeline/genome/Bra_Chiifu_v4.0.gtf"
cpu=9
cat $sample |while read sra;
do
        mkdir -p ${clean_dir}/${sra}
		prefetch.3.1.0 ${sra} --output-directory $sra_dir --max-size 500G
		fasterq-dump.3.1.0 -e $cpu -3 $sra_dir/$sra/${sra}.sra -O $raw_dir/$sra/ -t $raw_dir/$sra/ 
		#gzip $raw_dir/$sra/*
		if grep -q "^${sra}$" "$SINGLE_LIST"; then
				fastp -i ${raw_dir}/${sra}/${sra}.fastq -o ${clean_dir}/${sra}/${sra}.clean.fastq.gz -w $cpu -j logs/${sra}.json -h logs/${sra}.html
				sh $wk/hisat2_single.sh $ref $gtf ${clean_dir}/${sra}/${sra}.clean.fastq.gz $cpu $sra 1>logs/${sra}.out 2>logs/${sra}.err
        else
				fastp -i ${raw_dir}/${sra}/${sra}_1.fastq -I ${raw_dir}/${sra}/${sra}_2.fastq -w $cpu -o ${clean_dir}/${sra}/${sra}_1.clean.fastq.gz -O ${clean_dir}/${sra}/${sra}_2.clean.fastq.gz -j logs/${sra}.json -h logs/${sra}.html
                sh $wk/hisat2.sh $ref $gtf ${clean_dir}/${sra}/${sra}_1.clean.fastq.gz ${clean_dir}/${sra}/${sra}_2.clean.fastq.gz $cpu $sra 1>logs/${sra}.out 2>logs/${sra}.err 
        fi
        rm -rf ${clean_dir}/${sra}
        rm -rf ${raw_dir}/${sra}
		echo ${sra} >> done.list
done
