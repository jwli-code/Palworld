"""<br>
Author: jwli && lnzhang<br>
Institution: Huazhong Agricultural University<br>
Description: Pipeline from downloading SRA data to calculating gene expression.<br>
"""<br>
<h4>hisat2 + stringtie</h4> <br>
<br>
1.list.txt         A list of all SRA numbers<br>
2.single.list      A list of all single-ended sequencing SRA numbers<br>
3.Prepare the fa and gtf files to build indexes into the genome<br>
4.sh run split.sh<br>
5.sh run_pipeline.sh<br>

<br>
<h4>Filter representative data from a large number of RNAseq data according to the greedy algorithm</h4> <br>
Example:
<br>
python expression_to_num.py Bju.tpm.txt Bju.tpm.txt2
<br>
python find_represent_SRA.py Bju.tpm.txt2 Bju_represent_50.txt 50
