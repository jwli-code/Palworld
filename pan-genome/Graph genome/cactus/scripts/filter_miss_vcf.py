import sys

# Script Description:
# This script filters a VCF file to retain rows where the number of missing values 
# (represented by ".") in the 10th and subsequent columns is less than to a specified threshold.
# It prints all header lines (starting with "#") and any data lines meeting the missing value condition.
# Usage: python filter_missing.py <input_vcf> <max_missing_count>
# Where <input_vcf> is the path to the input VCF file, and <max_missing_count> is the maximum allowed number of missing values.

# Check command line arguments
if len(sys.argv) < 3:
    print("Usage: python filter_missing.py <input_vcf> <max_missing_count>", file=sys.stderr)
    sys.exit(1)

input_vcf = sys.argv[1]
max_missing_count = int(sys.argv[2])

with open(input_vcf, 'r') as infile:
    for line in infile:
        if line.startswith('#'):
            print(line, end='')
        else:
            parts = line.strip().split('\t')
            # Count missing values in the 10th and subsequent columns
            if parts[9:].count('.') <= max_missing_count:
                print(line, end='')
