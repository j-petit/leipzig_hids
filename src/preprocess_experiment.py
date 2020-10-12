import os
from datetime import datetime
import pprint
import glob
import logging
import pickle
from pprint import pformat
import sys
import yaml
import pathpy
import pandas as pd
import dotenv

import sacred

from src.data_processing import process_raw_temporal_dataset, get_runs
from src.utils import config_adapt


def preprocess(config):

    log = pathpy.utils.Log
    log.set_min_severity(config["pathpy"]["min_severity"])

    results_logger = logging.getLogger("make_temp_paths")
    log_file = os.path.join(config["c_results"]["output_path"], "ex_make_temp_paths.log")
    hdlr = logging.FileHandler(log_file, mode="w")
    results_logger.addHandler(hdlr)

    time_delta = config["model"]["time_delta"]

    train, _ = create_train_test_split(config["data"]["runs"], config["model"]["train_examples"])

    runs = get_runs(config["data"]["runs"], train)

    results_logger.info("runs for training")
    results_logger.info(runs)

    paths = process_raw_temporal_dataset(runs, time_delta)

    pickle.dump(
        paths, open(config["model"]["paths"], "wb"),
    )

    results_logger.info(paths)


def create_train_test_split(runs: str, num_train: int):

    all_runs = pd.read_csv(runs, skipinitialspace=True)
    train_runs = all_runs[all_runs["is_executing_exploit"] == False].head(num_train)
    train = train_runs.index
    test_runs = all_runs.loc[~all_runs.index.isin(train)]
    test = test_runs.index

    return train, test
