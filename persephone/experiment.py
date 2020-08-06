""" Miscellaneous functions for experiment management. """

import os

from typing import Optional

import persephone
from . import config
from . import rnn_ctc
from .corpus_reader import CorpusReader

EXP_DIR = config.EXP_DIR # type: str

def get_exp_dir_num(parent_dir: str) -> int:
    """ Gets the number of the current experiment directory."""
    return max([int(fn.split(".")[0])
                for fn in os.listdir(parent_dir) if fn.split(".")[0].isdigit()]
                    + [-1])

def _prepare_directory(directory_path: str) -> str:
    """
    Prepare the directory structure required for the experiment
    :returns: returns the name of the newly created directory
    """
    exp_num = get_exp_dir_num(directory_path)
    exp_num = exp_num + 1
    exp_dir = os.path.join(directory_path, str(exp_num))
    if not os.path.isdir(exp_dir):
        os.makedirs(exp_dir)
    return exp_dir

def prep_sub_exp_dir(parent_dir: str) -> str:
    """ Prepares an experiment subdirectory
    :parent_dir: the parent directory
    :returns: returns the name of the newly created subdirectory
    """
    return _prepare_directory(parent_dir)

def prep_exp_dir(directory=EXP_DIR):
    """ Prepares an experiment directory by copying the code in this directory
    to it as is, and setting the logger to write to files in that directory.
    Stores the version of persephone used to run the experiment for diagnostic purposes.
    :directory: The path to directory we are preparing for the experiment,
                which will be created if it does not currently exist.
    :returns: The name of the newly created experiment directory.
    """
    if not os.path.isdir(directory):
        os.makedirs(directory)
    exp_dir = _prepare_directory(directory)
    # We assume the package was probably installed via pypi. Get the version
    # number.
    with open(os.path.join(exp_dir, "version.txt"), "w") as f:
        print("Persephone version {}".format(persephone.__version__), file=f)

    return exp_dir

def get_simple_model(exp_dir, corpus):
    num_layers = 2
    hidden_size= 250

    def decide_batch_size(num_train):

        if num_train >= 512:
            batch_size = 16
        elif num_train < 128:
            if num_train < 4:
                batch_size = 1
            else:
                batch_size = 4
        else:
            batch_size = int(num_train / 32)

        return batch_size

    batch_size = decide_batch_size(len(corpus.train_prefixes))

    corpus_reader = CorpusReader(corpus, batch_size=batch_size)
    model = rnn_ctc.Model(exp_dir, corpus_reader,
                          num_layers=num_layers,
                          hidden_size=hidden_size,
                          decoding_merge_repeated=True)

    return model

def train_ready(corpus, directory=EXP_DIR):

    print(directory)

    exp_dir = prep_exp_dir(directory=directory)
    model = get_simple_model(exp_dir, corpus)
    model.train(min_epochs=20, early_stopping_steps=3)
    return exp_dir

def transcribe(model_path, corpus, write_to_file=True):
    """ Applies a trained model to untranscribed data in a Corpus. """

    exp_dir = prep_exp_dir()
    model = get_simple_model(exp_dir, corpus)
    return_str = model.transcribe(model_path, write_to_file=write_to_file)

    return return_str
