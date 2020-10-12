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


project_dir = os.path.join(os.path.dirname(__file__), os.pardir)
dotenv_path = os.path.join(project_dir, ".env")
dotenv.load_dotenv(dotenv_path)

URI = "mongodb://{}:{}@139.18.13.64/?authSource=hids&authMechanism=SCRAM-SHA-1".format(
    os.environ["SACRED_MONGODB_USER"], os.environ["SACRED_MONGODB_PWD"]
)

ex = sacred.Experiment("hids_preprocess")
ex.observers.append(sacred.observers.MongoObserver(url=URI, db_name="hids"))


@ex.config_hook
def hook(config, command_name, logger):
    config = config_adapt(config)
    config.update({'hook': True})
    return config


@ex.command(unobserved=True)
def print_config(_config):
    """ Replaces print_config which is not working with python 3.8 and current packages sacred"""
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(_config)


@ex.automain
def preprocess(hook, _config):

    log = pathpy.utils.Log
    log.set_min_severity(_config["pathpy"]["min_severity"])

    results_logger = logging.getLogger("make_temp_paths")
    log_file = os.path.join(_config["c_results"]["output_path"], "ex_make_temp_paths.log")
    hdlr = logging.FileHandler(log_file, mode="w")
    results_logger.addHandler(hdlr)

    time_delta = _config["model"]["time_delta"]

    train, _ = create_train_test_split(_config["data"]["runs"], _config["model"]["train_examples"])

    runs = get_runs(_config["data"]["runs"], train)

    results_logger.info("runs for training")
    results_logger.info(runs)

    paths = process_raw_temporal_dataset(runs, time_delta)

    pickle.dump(
        paths, open(_config["model"]["paths"], "wb"),
    )

    results_logger.info(paths)


def create_train_test_split(runs: str, num_train: int):

    all_runs = pd.read_csv(runs, skipinitialspace=True)
    train_runs = all_runs[all_runs["is_executing_exploit"] == False].head(num_train)
    train = train_runs.index
    test_runs = all_runs.loc[~all_runs.index.isin(train)]
    test = test_runs.index

    return train, test
