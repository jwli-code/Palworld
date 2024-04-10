mkdir splitfile
tail -n +2 SRR1228210.tab |awk '{print $1}'|sort -k1  >temp.txt
sed -i "1i geneID" temp.txt
cat Bra.list |while read line;
do
tail -n +2 ${line}.tab | awk '{print $1, $NF}' | sort -k1 |awk '{print $2}' > splitfile/${line}.sort.txt
sed -i "1i ${line}" "splitfile/${line}.sort.txt"

paste temp.txt "splitfile/${line}.sort.txt" > temp2.txt
mv temp2.txt temp.txt
done
mv temp.txt >Bra_tpm.txt
