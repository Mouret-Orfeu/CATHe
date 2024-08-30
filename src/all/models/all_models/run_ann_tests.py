import os
import itertools
from tqdm import tqdm



def run_script_with_combinations(script_path, dropout_values, layer_size_values, nb_layer_block_values, input_type_values, pLDDT_threshold_values, model_values, combinations_to_skip=None):
    """
    Function to create all possible combinations of parameters and run a script for each combination.

    :param script_path: Path to the Python script to be run.
    :param dropout_values: List of possible dropout values.
    :param layer_size_values: List of possible layer size values.
    :param nb_layer_block_values: List of possible Nb_Layer_Block values.
    :param input_type_values: List of possible Input_Type values.
    :param pLDDT_threshold_values: List of possible pLDDT_threshold values.
    :param model_values: List of model names to use.
    :param combinations_to_skip: List of tuples representing parameter combinations to skip (optional).
    """
    if combinations_to_skip is None:
        combinations_to_skip = []

    # Create all possible combinations of parameters
    combinations = list(itertools.product(dropout_values, layer_size_values, nb_layer_block_values, input_type_values, pLDDT_threshold_values, model_values))

    # Iterate over each combination and run the script with a progress bar
    for dropout, layer_size, nb_layer_block, input_type, pLDDT_threshold, model in tqdm(combinations, desc="Running configurations"):
        
        # Skip the specified combinations
        if (dropout, layer_size, nb_layer_block, input_type, pLDDT_threshold, model) in combinations_to_skip:
            continue

        # Create the command to execute
        command = (f"python {script_path} --classifier_input {input_type} --dropout {dropout} "
                   f"--layer_size {layer_size} --nb_layer_block {nb_layer_block} "
                   f"--pLDDT_threshold {pLDDT_threshold} --model {model}")
        
        # Print the command (optional)
        print(f"Running: {command}")
        
        # Execute the command
        os.system(command)


script_path = './src/all/models/all_models/ann_all_models.py'


# Initialize the progress bar
total_runs = 3  # Number of different configurations/runs we have
progress_bar = tqdm(total=total_runs, desc="Overall Progress")

# Run each configuration setup and update the progress bar
# 1. Dropout analysis setup
dropout_values = [0.1,0.5,0.7]
layer_size_values = [1024]
nb_layer_block_values = ['two']
input_type = ['3Di']
pLDDT_threshold = [0]
model = ['ProstT5_full']

run_script_with_combinations(script_path, dropout_values, layer_size_values, nb_layer_block_values, input_type, pLDDT_threshold, model)
progress_bar.update(1)
print(f"{progress_bar.n} run(s) have terminated.")

# 2. Layer size analysis setup
dropout_values = [0, 0.7]
layer_size_values = [1024]
nb_layer_block_values = ['two']
input_type = ['AA']
pLDDT_threshold = [0]
model = ['ProstT5_full']

run_script_with_combinations(script_path, dropout_values, layer_size_values, nb_layer_block_values, input_type, pLDDT_threshold, model)
progress_bar.update(1)
print(f"{progress_bar.n} run(s) have terminated.")

# 3. Nb layer block analysis setup
dropout_values = [0,0.1, 0.2]
layer_size_values = [1024]
nb_layer_block_values = ['two']
input_type = ['AA+3Di']
pLDDT_threshold = [0]
model = ['ProstT5_full']

run_script_with_combinations(script_path, dropout_values, layer_size_values, nb_layer_block_values, input_type, pLDDT_threshold, model)
progress_bar.update(1)
print(f"{progress_bar.n} run(s) have terminated.")

# Close the progress bar after all runs
progress_bar.close()



# # Create all possible combinations of parameters
# combinations = list(itertools.product(dropout_values, layer_size_values, nb_layer_block_values, input_type, pLDDT_threshold, model))


# # Iterate over each combination and run the script with a progress bar
# for dropout, layer_size, nb_layer_block, input_type, pLDDT_threshold, model in tqdm(combinations, desc="Running configurations"):

#     # # Skip the specified combinations
#     # if (dropout, layer_size, nb_layer_block) in combinations_to_skip:
#     #     continue

#     command = f"python {script_path} --classifier_input {input_type} --dropout {dropout} --layer_size {layer_size} --nb_layer_block {nb_layer_block} --pLDDT_threshold {pLDDT_threshold} --model {model}"
#     print(f"Running: {command}")
#     os.system(command)