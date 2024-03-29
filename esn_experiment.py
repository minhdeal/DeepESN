import argparse
import json
import logging
import numpy as np
import os

from scoop import futures

import deepesn

# Initialize logger
logger = logging.getLogger(__name__)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

###############################################################################################
# The next part needs to be in the global scope, since all workers
# need access to these variables. I got pickling problems when using
# them as arguments in the evaluation function. I couldn't pickle the
# partial function for some reason, even though it should be supported.
############################################################################
# Parse input arguments
############################################################################
parser = argparse.ArgumentParser()
parser.add_argument("data", help="path to data file", type=str)
parser.add_argument("esnconfig", help="path to ESN config file", type=str)
parser.add_argument("reconstructconfig", help="path to reconstruct config file", type=str)
parser.add_argument("nexp", help="number of runs", type=int)
args = parser.parse_args()

############################################################################
# Read config file
############################################################################
config = json.load(open(args.esnconfig + '.json', 'r'))
reconstructconfig = json.load(open(args.reconstructconfig + '.json', 'r'))

############################################################################
# Load data
############################################################################
# If the data is stored in a directory, load the data from there. Otherwise,
# load from the single file and split it.

dataType = args.data.split('/')[-1]

if os.path.isdir(args.data):
    Xtr, Ytr, _, _, Xte, Yte, Yscaler = deepesn.load_from_dir(args.data)

elif dataType=='SantaFe':
    #Xtr, Ytr, _, _, Xte, Yte, Yscaler = esnet.generate_datasets_santafe(args.data)
    X, Y = deepesn.load_from_text(args.data)

    # Construct training/test sets
    Xtr, Ytr, _, _, Xte, Yte, Yscaler = deepesn.generate_datasets(X, Y)

    Xtr, Xte = deepesn.reconstruct_input_santafe([Xtr, Xte], reconstructconfig)
    Ytr, Yte = deepesn.reconstruct_output_santafe([Ytr, Yte], reconstructconfig)

else:
    X, Y = deepesn.load_from_text(args.data)

    # Construct training/test sets
    Xtr, Ytr, _, _, Xte, Yte, Yscaler = deepesn.generate_datasets(X, Y)

    # Reconstruct
    Xtr, Xte = deepesn.reconstruct_input([Xtr, Xte], reconstructconfig)
    Ytr, Yte = deepesn.reconstruct_output([Ytr, Yte], reconstructconfig)

def single_run(dummy):
    """
    This function will be run by the workers.
    """
    _,error = deepesn.run_from_config(Xtr, Ytr, Xte, Yte, config, Yscaler)

    return error

def main():
    # Run in parallel and store result in a numpy array
    errors = np.array(list(map(single_run, range(args.nexp))), dtype=float)

    print("Errors:")
    print(errors)

    print("Mean:")
    print(np.mean(errors))

    print("Std:")
    print(np.std(errors))

if __name__ == "__main__":
    main()
