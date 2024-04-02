module load Singularity/3.7.3
seq=Bna_14.seq
cpu=30
mkdir log
bsub -J cactus_Bna -q smp -n 30 -R span[hosts=1] -o  log/cactus.out -e log/cactus.err \
"
singularity exec -B ${PWD}:${PWD} ${PWD}/cactus_v2.6.8.sif cactus-pangenome ${PWD}/js ${PWD}/$seq --outDir ${PWD}/Bna_14.pg --outName Bna_14-pg --reference ZS11 --vcf --giraffe --gfa --gbz --maxCores $cpu --permissiveContigFilter
"
