module load jcvi/1.0.6
mkdir BGI_diamond
mkdir Uniprot_func_GO
diamond blastp -d uniprot_plants.dmnd -q ${pep}/${line}.pep --evalue 1e-5 -p 10 -o ./BGI_diamond/${line}.hit
python -m jcvi.formats.blast best -n 1 ./BGI_diamond/${line}.hit
python add_annotation_from_dat.py ${hit}/${line}.hit.best uniprot_plants.dat ./Uniprot_func_GO/${line}_unipro_function_GO.txt
