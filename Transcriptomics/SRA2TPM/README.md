"""<br>
Author: jwli && lnzhang<br>
Institution: Huazhong Agricultural University<br>
Description: Pipeline from downloading SRA data to calculating gene expression.<br>
"""<br>
hisat2 + stringtie <br>
<br>
1.list.txt         A list of all SRA numbers<br>
2.single.list      A list of all single-ended sequencing SRA numbers<br>
3.Prepare the fa and gtf files to build indexes into the genome<br>
4.sh run split.sh<br>
5.sh run_pipeline.sh<br>
