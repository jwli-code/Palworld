###Author:jwli
安装教程
micromamba install -c hcc aspera-cli
$ which ascp # 输出下面内容，不同环境不一样，根据自己的来
~/software/miniconda3/envs/test/bin/ascp
把bin及bin后面的内容换成etc/asperaweb_id_dsa.openssh可以用 ls验证一下是否存在。
$ ls ~/software/miniconda3/envs/test/etc/asperaweb_id_dsa.openssh
/home/wwwdj/software/miniconda3/envs/test/etc/asperaweb_id_dsa.openssh

### ascp_fastq.sh脚本内容
echo -e "\n\n\n 000# ascp Download FASTQ !!! \n\n\n"
## 密匙路径
openssh=~/miniconda3/etc/asperaweb_id_dsa.openssh

cat sample.txt | while read id
do
num=`echo $id | wc -m ` #这里注意，wc -m 会把每行结尾$也算为一个字符
echo "SRRnum+1 is $num" #因此SRRnum + 1才等于$num值
#如果样本编号为SRR+8位数 #
if [ $num -eq 12 ]
then
        echo "SRR + 8"
        x=$(echo $id | cut -b 1-6)
        y=$(echo $id | cut -b 10-11)
        echo "Downloading $id "
        ( ascp  -QT -l 500m -P33001  -k 1 -i $openssh \
                era-fasp@fasp.sra.ebi.ac.uk:vol1/fastq/$x/0$y/$id/   ./ & )
#如果样本编号为SRR+7位数 #
elif [ $num -eq 11 ]
then
        echo  "SRR + 7"
        x=$(echo $id | cut -b 1-6)
        y=$(echo $id | cut -b 10-10)
        echo "Downloading $id "
        ( ascp  -QT -l 500m -P33001  -k 1 -i $openssh \
                        era-fasp@fasp.sra.ebi.ac.uk:vol1/fastq/$x/00$y/$id/   ./ & )
#如果样本编号为SRR+6位数 #
elif [ $num -eq 10 ]
then
        echo  "SRR + 6"
        x=$(echo $id |cut -b 1-6)
        echo "Downloading $id "
        ( ascp  -QT -l 500m -P33001 -k 1 -i  $openssh \
                        era-fasp@fasp.sra.ebi.ac.uk:vol1/fastq/$x/$id/   ./ & )
fi
done
