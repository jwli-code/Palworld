miniprot -t 20 -d Bna_ZS11_v0.0.mpi Bna_ZS11_v0.0.fasta
miniprot -t 20 -Iu --gff Bna_ZS11_v0.0.mpi ${line}.pep >../result/${line}.gff
