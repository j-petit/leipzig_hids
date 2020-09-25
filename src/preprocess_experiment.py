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
from src.utils import load_config

project_dir = os.path.join(os.path.dirname(__file__), os.pardir)
dotenv_path = os.path.join(project_dir, ".env")
dotenv.load_dotenv(dotenv_path)

URI = "mongodb://{}:{}@139.18.13.64/?authSource=hids&authMechanism=SCRAM-SHA-1".format(
    os.environ["SACRED_MONGODB_USER"], os.environ["SACRED_MONGODB_PWD"]
)

ex = sacred.Experiment("hids_preprocess")
ex.observers.append(sacred.observers.MongoObserver(url=URI, db_name="hids"))
config = load_config("config/config.yaml")
ex.add_config(config)

@ex.command(unobserved=True)
def print_config(_config):
    """ Replaces print_config which is not working with python 3.8 and current packages sacred"""
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(_config)


@ex.automain
def preprocess(_config, _log):

    config = _config

    log = pathpy.utils.Log
    log.set_min_severity(config["pathpy"]["min_severity"])

    time_delta = config["model"]["time_delta"]

    intermediate_directory = config["data"]["processed"]

    os.makedirs(intermediate_directory, exist_ok=True)

    train, _ = create_train_test_split(config["data"]["runs"], config["model"]["train_examples"])

    runs = get_runs(config["data"]["runs"], train)

    paths = process_raw_temporal_dataset(runs, time_delta)

    pickle.dump(
        paths, open(os.path.join(intermediate_directory, f"temp_paths_{time_delta}.p"), "wb"),
    )

    _log.info(paths)
    _log.info("Creating multi order model now...")

    mom = pathpy.MultiOrderModel(paths, max_order=config["model"]["max_order"])
    order = mom.estimate_order()
    mom = pathpy.MultiOrderModel(paths, max_order=order)

    os.makedirs(config["model"]["save"], exist_ok=True)

    pickle.dump(
        mom, open(os.path.join(config["model"]["save"], f"MOM_{order}_delta_{time_delta}.p"), "wb"),
    )

    _log.info(mom)


def create_train_test_split(runs: str, num_train: int):

    all_runs = pd.read_csv(runs, skipinitialspace=True)
    train_runs = all_runs[all_runs["is_executing_exploit"] == False].head(num_train)
    train = train_runs.index
    test_runs = all_runs.loc[~all_runs.index.isin(train)]
    test = test_runs.index

    return train, test
