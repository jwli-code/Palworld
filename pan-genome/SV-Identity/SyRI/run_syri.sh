ref=$1
qry=$2
nucmer -t 15 ${ref} ${qry}      # Whole genome alignment. Any other alignment can also be used.
delta-filter -m -i 90 -l 100 out.delta >out.filtered.delta     # Remove small and lower quality alignments
show-coords -THrd out.filtered.delta >out.filtered.coords      # Convert alignment information to a .TSV format as required by SyRI
syri -c out.filtered.coords -d out.filtered.delta -r ${ref} -q ${qry}
/home/jwli/2024/NG_Bol/study/05_SV/syri/syri/bin/plotsr syri.out ${ref} ${qry} -H 8 -W 5
