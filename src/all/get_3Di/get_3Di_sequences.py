import pandas as pd
import requests
import subprocess
import os
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
from Bio.PDB import PDBParser, PDBIO, Select
from Bio.SeqUtils import seq1
import warnings
from Bio import BiopythonWarning
import argparse

warnings.simplefilter('ignore', BiopythonWarning)

# Function to remove 'X' from sequences
def clean_sequence(sequence):
    return sequence.replace('X', '')

# Function to compare sequences
def compare_sequences(csv_sequence, pdb_sequence):
    return csv_sequence == pdb_sequence

class TrimSelect(Select):
    def __init__(self, residues):
        self.residues = residues

    def accept_residue(self, residue):
        return residue in self.residues

def trim_pdb(pdb_file_path, sequence, chain_id, model_id):
    parser = PDBParser()
    structure = parser.get_structure('structure', pdb_file_path)
    
    # Convert sequence to a set of residues to keep
    seq_residues = set()
    seq_index = 0
    untrimmed_sequence = ''
    for model in structure:
        if model.id == model_id:  # Check if model matches
            for chain in model:
                if chain.id == chain_id:  # Check if chain matches
                    for residue in chain:
                        res_name = seq1(residue.resname)
                        untrimmed_sequence += res_name
                        if seq_index < len(sequence) and res_name == sequence[seq_index]:
                            seq_residues.add(residue)
                            seq_index += 1
                        if seq_index == len(sequence):
                            break

    # Write out the trimmed structure
    io = PDBIO()
    io.set_structure(structure)
    trimmed_pdb_file_path = pdb_file_path.replace('.pdb', '_trimmed.pdb')
    io.save(trimmed_pdb_file_path, select=TrimSelect(seq_residues))
    
    # Verify the trimmed PDB file
    pdb_sequence = extract_sequence_from_pdb(trimmed_pdb_file_path, chain_id, model_id)
    if not compare_sequences(clean_sequence(sequence), pdb_sequence):
        raise ValueError(f"Sequence mismatch for PDB ID {pdb_file_path}.\nCSV sequence: {sequence}\nPDB trimmed sequence: {pdb_sequence}\nUntrimmed PDB sequence: {untrimmed_sequence}")
    
    return trimmed_pdb_file_path

# Function to download and trim a PDB file given a PDB ID and chain
def download_and_trim_pdb(row, output_dir):
    sequence_id = row['Unnamed: 0']
    sequence = clean_sequence(row['Sequence'])
    domain = row['Domain']
    pdb_id = domain[:4]  # Extract the first 4 characters as PDB ID
    chain = domain[4]  # Extract the 5th character as the chain
    model_id = int(domain[5:])  # Extract the 6th character as the model ID (format example '02')

    url = f"https://files.rcsb.org/download/{pdb_id}.pdb"
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise an exception for HTTP errors
        pdb_file_path = os.path.join(output_dir, f"{sequence_id}_{pdb_id}.pdb")
        with open(pdb_file_path, 'w') as file:
            file.write(response.text)
        
        # Trim the PDB file
        trimmed_pdb_file_path = trim_pdb(pdb_file_path, sequence, chain, model_id)
        
        # Remove the original untrimmed file
        os.remove(pdb_file_path)
        
        return {"sequence_id": sequence_id, "pdb_file": trimmed_pdb_file_path}
    except requests.exceptions.HTTPError as http_err:
        print(f"HTTP request failed: {http_err}")
        return {"sequence_id": sequence_id, "pdb_file": None}
    except ValueError as val_err:
        print(val_err)
        return {"sequence_id": sequence_id, "pdb_file": None}
    except Exception as err:
        print(f"Other error occurred: {err}")
        return {"sequence_id": sequence_id, "pdb_file": None}

# Function to extract sequence from PDB file
def extract_sequence_from_pdb(pdb_file_path, chain_id, model_id):
    parser = PDBParser()
    structure = parser.get_structure('structure', pdb_file_path)
    sequence = ''
    chain_model_found = False
    for model in structure:
        if model.id == model_id:  # Check if model matches
            for chain in model:
                if chain.id == chain_id:  # Check if chain matches
                    chain_model_found = True
                    for residue in chain:
                        if residue.id[0] == ' ':  # Ensures only standard residues are considered
                            sequence += seq1(residue.resname)

    if not chain_model_found:
        raise ValueError(f"Chain {chain_id} of model {model_id} not found in PDB file {pdb_file_path}")
    return sequence

# Function to run a shell command and check for errors
def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running command: {command}")
        print(result.stderr)
        raise Exception("Command failed")
    return result.stdout

# Create an ArgumentParser
def create_arg_parser():
    parser = argparse.ArgumentParser(description='Process dataset to extract 3Di sequences.')
    parser.add_argument('--dataset', type=str, choices=['all', 'test', 'train', 'validation'], default='all',
                        help="Dataset to process: 'all', 'test', 'train', 'validation'")
    return parser

def process_dataset(data, output_dir, query_db, query_db_ss_fasta):
    os.makedirs(output_dir, exist_ok=True)

    results = []
    with ThreadPoolExecutor(max_workers=20) as executor:
        futures = [executor.submit(download_and_trim_pdb, row, output_dir) for _, row in data.iterrows()]
        for future in tqdm(as_completed(futures), total=len(futures)):
            result = future.result()
            results.append(result)

    results_df = pd.DataFrame(results)
    output_csv = os.path.join(output_dir, 'directly_saved_pdb_idx.csv')
    results_df.to_csv(output_csv, index=False)

    print(f"Download completed and results saved to {output_csv}")

    try:
        run_command(f"foldseek createdb {output_dir} {query_db}")
        run_command(f"foldseek lndb {query_db}_h {query_db}_ss_h")
        run_command(f"foldseek convert2fasta {query_db}_ss {query_db_ss_fasta}")
        print(f"FASTA file created at {query_db_ss_fasta}")

    except Exception as e:
        print(f"An error occurred: {e}")

    # Remove intermediate and PDB files
    os.remove(query_db + '_a3m')
    os.remove(query_db + '_ss')
    os.remove(query_db + '_ss_h')
    os.remove(query_db + '_h')
    for file in os.listdir(output_dir):
        file_path = os.path.join(output_dir, file)
        os.remove(file_path)


def main():
    # Parse arguments
    parser = create_arg_parser()
    args = parser.parse_args()

    dataset_map = {
        'test': './data/Dataset/csv/Test.csv',
        'train': './data/Dataset/csv/Train.csv',
        'validation': './data/Dataset/csv/Validation.csv'
    }

    datasets_to_process = dataset_map.values() if args.dataset == 'all' else [dataset_map[args.dataset]]

    for csv_file in datasets_to_process:
        data = pd.read_csv(csv_file)
        dataset_name = os.path.basename(csv_file).split('.')[0]

        if dataset_name == 'Train':
            half_index = len(data) // 2
            data_first_half = data.iloc[:half_index]
            data_second_half = data.iloc[half_index:]

            output_dir_first = f'./data/pdb_files/{dataset_name}_first'
            query_db_first = f'./data/pdb_files/{dataset_name}_first_queryDB'
            query_db_ss_fasta_first = f'./data/Dataset/3Di/{dataset_name}_first.fasta'

            output_dir_second = f'./data/pdb_files/{dataset_name}_second'
            query_db_second = f'./data/pdb_files/{dataset_name}_second_queryDB'
            query_db_ss_fasta_second = f'./data/Dataset/3Di/{dataset_name}_second.fasta'

            process_dataset(data_first_half, output_dir_first, query_db_first, query_db_ss_fasta_first)
            process_dataset(data_second_half, output_dir_second, query_db_second, query_db_ss_fasta_second)

            final_fasta_path = f'./data/Dataset/3Di/{dataset_name}.fasta'
            with open(final_fasta_path, 'w') as final_fasta:
                with open(query_db_ss_fasta_first, 'r') as first_fasta:
                    final_fasta.write(first_fasta.read())
                with open(query_db_ss_fasta_second, 'r') as second_fasta:
                    final_fasta.write(second_fasta.read())

            os.remove(query_db_ss_fasta_first)
            os.remove(query_db_ss_fasta_second)

            print(f"Merged FASTA file created at {final_fasta_path}")

        else:
            output_dir = f'./data/pdb_files/{dataset_name}'
            query_db = f'./data/pdb_files/{dataset_name}_queryDB'
            query_db_ss_fasta = f'./data/Dataset/3Di/{dataset_name}.fasta'

            process_dataset(data, output_dir, query_db, query_db_ss_fasta)

if __name__ == '__main__':
    main()