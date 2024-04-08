import argparse

def write_vcf_header(vcf_file, ref_fasta,name):
    """Writes the VCF header and contig information based on the reference FASTA."""
    vcf_file.write("##fileformat=VCFv4.2\n")
    vcf_file.write("##source=Syri\n")
    for contig, sequence in ref_fasta.items():
        vcf_file.write(f"##contig=<ID={contig},length={len(sequence)}>\n")
    vcf_file.write('##INFO=<ID=SVTYPE,Number=1,Type=String,Description="Type of the SV.">\n')
    vcf_file.write('##INFO=<ID=SVLEN,Number=1,Type=Integer,Description="Length of the SV">\n')
    vcf_file.write('##FORMAT=<ID=GT,Number=1,Type=String,Description="Genotype">\n')
    vcf_file.write(f"#CHROM\tPOS\tID\tREF\tALT\tQUAL\tFILTER\tINFO\tFORMAT\t{name}\n")

def read_fasta(file_path):
    """Reads a FASTA file and returns a dictionary with sequence identifiers as keys and sequences as values."""
    sequences = {}
    current_seq_name = None
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line.startswith('>'):
                current_seq_name = line[1:].split()[0]  # Assume ID is the first part of the header line
                sequences[current_seq_name] = []
            else:
                sequences[current_seq_name].append(line)
    for seq_name in sequences.keys():
        sequences[seq_name] = ''.join(sequences[seq_name])  # Concatenate list of sequences into a single string
    return sequences

def reverse_complement(seq):
    """Returns the reverse complement of a DNA sequence."""
    complement = {'A': 'T', 'T': 'A', 'C': 'G', 'G': 'C', 'N': 'N'}
    return ''.join([complement[base] for base in reversed(seq)])

def extract_sequence(fasta_dict, chrom, start, end, strand):
    """Extracts a sequence from the given chromosome and coordinates, and returns the reverse complement if needed."""
    sequence = fasta_dict[chrom][start-1:end]
    if strand == '-':
        sequence = reverse_complement(sequence)
    return sequence

def bed_to_vcf_line(fields, ref_fasta, query_fasta, max_len, name):
    """Converts a line from BED format to VCF format."""
    ref_chr, ref_start, ref_end, _, _, query_chr, query_start, query_end, _, _, sv_type = fields[:11]
    # Filter out non-matching chromosomes and unwanted SV types
    if ref_chr != query_chr or sv_type not in {"CPL", "INS", "DEL", "CPG"}:
        return None
    ref_start, ref_end, query_start, query_end = int(ref_start), int(ref_end), int(query_start), int(query_end)
    ref_seq = extract_sequence(ref_fasta, ref_chr, ref_start, ref_end, '+')  # Reference sequence is assumed to be on the '+' strand
    alt_seq = extract_sequence(query_fasta, query_chr, query_start, query_end, '+')
    svlen = abs(len(alt_seq) - len(ref_seq))  # Calculate SV length
    if svlen > max_len:
        return None
    if svlen <= 50:
        return None
    # Adjust sv_type if necessary
    if sv_type == "CPG":
        sv_type = "INS"
    elif sv_type == "CPL":
        sv_type = "DEL"
    # Construct INFO field with SVTYPE and SVLEN
    info_field = f"SVTYPE={sv_type};SVLEN={svlen}"
    ID=f"{name}_{ref_chr}_{ref_start}"
    return f"{ref_chr}\t{ref_start}\t{ID}\t{ref_seq}\t{alt_seq}\t.\tPASS\t{info_field}\tGT\t1/1"

def process_bed_file(bed_path, ref_fasta_path, query_fasta_path, output_path, max_len, name):
    """Processes the given BED file and writes the output to a VCF file."""
    ref_fasta = read_fasta(ref_fasta_path)
    query_fasta = read_fasta(query_fasta_path)

    with open(bed_path, 'r') as bed_file, open(output_path, 'w') as vcf_file:
        # Write VCF header
        write_vcf_header(vcf_file, ref_fasta, name)
        # More headers can be added here

        for line in bed_file:
            fields = line.strip().split('\t')
            vcf_line = bed_to_vcf_line(fields, ref_fasta, query_fasta, max_len, name)
            if vcf_line:
                vcf_file.write(vcf_line + "\n")

def main():
    parser = argparse.ArgumentParser(description="Convert BED to VCF format.")
    parser.add_argument("-i", "--input", required=True, help="Input BED file")
    parser.add_argument("-r", "--ref", required=True, help="Reference FASTA file")
    parser.add_argument("-q", "--query", required=True, help="Query FASTA file")
    parser.add_argument("-o", "--output", required=True, help="Output VCF file")
    parser.add_argument("--max_len", type=int, default=100000, help="Maximum length of SV")
    parser.add_argument("--name",required=True, help="Sample name")
    args = parser.parse_args()

    process_bed_file(args.input, args.ref, args.query, args.output, args.max_len, args.name)

if __name__ == "__main__":
    main()
