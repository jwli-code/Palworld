#!/user/bin/env python
"""
Copyright (c) jwli.
HZAU
"""
import re
import sys
from Bio import SeqIO

if len(sys.argv) < 3:
    print("usage: add_annotation_from_dat.py blastp dat")
    sys.exit(1)

blastp_file = sys.argv[1]
dat = sys.argv[2]
output = sys.argv[3]

uniprot = SeqIO.index(dat, "swiss")

out_file = open(output, "w")

for line in open(blastp_file, "r"):
    gene,acc,ident = line.strip().split()[0:3]
    if not uniprot.get(acc.strip(";")):
        continue
    record = uniprot.get_raw(acc.strip(";"))
    record = record.decode('utf-8')
    GO_RECORD = re.findall(r"GO; (GO:\d+); ([F|P|C]):.*?; (.*):",record)
    GO_IDS = [go[0] for go in GO_RECORD]
    PFAM_RECORD = re.findall(r"DR\s+Pfam;\s+(\w+);\s+([^;]+);", record)
    PFAM_IDS = [pfam[0] for pfam in PFAM_RECORD]
    PFAM_DESCS = [pfam[1] for pfam in PFAM_RECORD]
    pfam_combined = ", ".join([f"{id}:{desc}" for id, desc in zip(PFAM_IDS, PFAM_DESCS)])
    # 从记录中提取RecName信息
    REC_NAME = re.findall(r"DE\s+RecName: Full=([^;{]+)", record)
    if len(REC_NAME):
        REC_NAME = [ REC_NAME[0].replace("\t"," ") ]
    else:
        REC_NAME = [""]
    SPECIES = re.findall(r"OS   (.*)\.", record)
    if len(SPECIES) == 0:
        SPECIES = [""]
    else:
        SPECIES = [ SPECIES[0].replace("\t"," ") ]
    merged_go_ids = ",".join(GO_IDS)
    #ENSEMBLE_Plant = re.findall(r"EnsemblPlants; (.*?);", record)
    #if len(ENSEMBLE_Plant) == 0:
    #    ENSEMBLE_Plant = [""]
    #else:
    #    ENSEMBLE_Plant = [ENSEMBLE_Plant[0].replace("\t"," ")]

    outline = "\t".join([gene, acc,ident] + SPECIES +REC_NAME + [merged_go_ids]+[pfam_combined])
    out_file.writelines(outline + "\n")

out_file.close()
