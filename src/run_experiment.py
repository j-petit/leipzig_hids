import os
from datetime import datetime
import pprint
import glob
import logging
import pickle
from pprint import pformat

from sacred import Experiment
from sacred.observers import MongoObserver
import pathpy
import pandas as pd

import pudb

from src.attack_simulate import trial_scenario
from src.data_processing import generate_temporal_network

logging.basicConfig(
    format="%(message)s", level=logging.INFO, datefmt="%H:%M:%S",
)

URI = "mongodb://jens:{}@139.18.13.64/?authSource=hids&authMechanism=SCRAM-SHA-1".format(
    os.environ["SACRED_MONGODB_PWD"]
)

ex = Experiment("hids")
ex.observers.append(MongoObserver(url=URI, db_name="hids"))
ex.logger = logging.getLogger("hids")


@ex.config
def my_config():

    # training params etc
    seed = 42

    exploit = False

    dataset = "CVE-2017-7529"
    data_prefix = "data"
    dataset_runs = os.path.join(data_prefix, dataset, "runs.csv")


    input_params = {
        "paths_pickle": "data/temp_paths_30.p",
        "attack": True,
    }

    input_params["scenario"] = get_scenario(dataset_runs, data_prefix, dataset, seed, exploit)

    training_params = {
        "learning_rate": 1e-3,
        "adam_eps": 1e-8,
        "eval_batch_size": 128,
        "train_batch_size": 128,
        "test_batch_size": 128,
        "num_epochs": 10,
    }

    # output
    output_prefix = "experiments"
    with_timestamp = False
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


    if with_timestamp:
        experiment_name = "{}_{}".format(dataset.upper(), timestamp)
    else:
        experiment_name = "{}".format(dataset.upper())

    output_path = os.path.join(output_prefix, experiment_name)
    os.makedirs(output_path, exist_ok=True)

    log_file = os.path.join(output_path, "general.log")
    hdlr = logging.FileHandler(log_file, mode="w")
    hdlr.setFormatter(logging.Formatter(fmt="%(asctime)s %(name)-12s %(levelname)-8s %(message)s"))
    ex.logger.addHandler(hdlr)


def get_scenario(dataset_runs, data_prefix, dataset, seed, exploit):
    runs = pd.read_csv(dataset_runs, skipinitialspace=True)
    attack_run = runs[runs["is_executing_exploit"] == exploit].sample(n=1, random_state=seed)
    return os.path.join(data_prefix, dataset, attack_run["scenario_name"].item() + ".txt")


@ex.command
def print_config_2(_config, unobserved=True):
    """ Replaces print_config which is not working with python 3.8 and current packages sacred"""
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(_config)


@ex.automain
def my_main(
    _log, training_params, _run, output_path, timestamp, dataset, data_prefix, dataset_runs, seed, input_params
):

    results_logger = logging.getLogger("results")
    results_logger.addHandler(
        logging.FileHandler(os.path.join(output_path, "results.log"), mode="w")
    )

    _log.info("Starting experiment at {}".format(timestamp))

    paths = pickle.load(open(input_params["paths_pickle"], "rb"))

    print(paths)

    hon_2_null = pathpy.HigherOrderNetwork(paths, k=2, null_model=True, separator='|')

    print(hon_2_null.summary())

    all_paths = pathpy.HigherOrderNetwork.generate_possible_paths(hon_2_null, 1)

    print(all_paths[0])

    for path in all_paths:
        paths.add_path(path)

    hon_2 = pathpy.HigherOrderNetwork(paths, k=2)
    print(hon_2.summary())

    likelihoods = trial_scenario(hon_2, input_params["scenario"], 10, 2000)

    for likelihood in likelihoods:
        _run.log_scalar("likelihood", likelihood[0], likelihood[1])

    ex.add_artifact(os.path.join(output_path, "results.log"))
