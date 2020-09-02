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
import dotenv

from src.attack_simulate import trial_scenario
from src.data_processing import generate_temporal_network


project_dir = os.path.join(os.path.dirname(__file__), os.pardir)
dotenv_path = os.path.join(project_dir, ".env")
dotenv.load_dotenv(dotenv_path)

URI = "mongodb://{}:{}@139.18.13.64/?authSource=hids&authMechanism=SCRAM-SHA-1".format(
    os.environ["SACRED_MONGODB_USER"], os.environ["SACRED_MONGODB_PWD"]
)

ex = Experiment("hids")
ex.observers.append(MongoObserver(url=URI, db_name="hids"))
ex.logger = logging.getLogger("hids")
ex.add_config("config/config.yaml")


@ex.config
def my_config(data, results, detector, seed):

    data["runs_abs"] = os.path.join(data["prefix"], data["name"], data["runs"])

    detector["model_abs"] = os.path.join(detector["prefix"], detector["model"])

    detector["scenario"] = get_scenario(
        data["runs_abs"], data["prefix"], data["name"], seed, detector["exploit"]
    )

    if results["timestamp"]:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        experiment_name = "{}_{}".format(data["name"].upper(), timestamp)
    else:
        experiment_name = "{}".format(data["name"].upper())

    results["output_path"] = os.path.join(results["prefix"], experiment_name)
    os.makedirs(results["output_path"], exist_ok=True)

    log_file = os.path.join(results["output_path"], "general.log")
    hdlr = logging.FileHandler(log_file, mode="w")
    hdlr.setFormatter(logging.Formatter(fmt="%(asctime)s %(name)-12s %(levelname)-8s %(message)s"))
    ex.logger.addHandler(hdlr)


def get_scenario(dataset_runs, data_prefix, dataset, seed, exploit):
    runs = pd.read_csv(dataset_runs, skipinitialspace=True)
    attack_run = runs[runs["is_executing_exploit"] == exploit].sample(n=1, random_state=seed)
    return os.path.join(data_prefix, dataset, attack_run["scenario_name"].item() + ".txt")


@ex.command
def print_config(_config, unobserved=True):
    """ Replaces print_config which is not working with python 3.8 and current packages sacred"""
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(_config)


@ex.automain
def my_main(
        _log,
        _run,
        detector,
        results,
        timestamp
):

    results_logger = logging.getLogger("results")
    results_logger.addHandler(
        logging.FileHandler(os.path.join(results["output_path"], "results.log"), mode="w")
    )

    _log.info("Starting experiment at {}".format(timestamp))

    paths = pickle.load(open(detector["model_abs"], "rb"))

    print(paths)

    hon_2_null = pathpy.HigherOrderNetwork(paths, k=2, null_model=True, separator="|")

    print(hon_2_null.summary())

    all_paths = pathpy.HigherOrderNetwork.generate_possible_paths(hon_2_null, 1)

    print(all_paths[0])

    for path in all_paths:
        paths.add_path(path)

    hon_2 = pathpy.HigherOrderNetwork(paths, k=2)
    print(hon_2.summary())

    likelihoods = trial_scenario(hon_2, detector["scenario"], 10, 2000)

    for likelihood in likelihoods:
        _run.log_scalar("likelihood", likelihood[0], likelihood[1])

    ex.add_artifact(os.path.join(results["output_path"], "results.log"))
