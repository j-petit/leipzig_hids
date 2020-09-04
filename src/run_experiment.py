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
from src.data_processing import generate_temporal_network, get_runs


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

    data["runs_abs"] = os.path.join(data["prefix"], data["raw"], data["name"], data["runs"])

    detector["model_abs"] = os.path.join(detector["prefix"], data["interim"], data["name"], detector["model"])

    detector["scenario"] = get_runs(data["runs_abs"], detector["exploit"]).sample(n=1, random_state=seed)["scenario_name"].item()

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
        timestamp,
        data
):

    results_logger = logging.getLogger("results")
    results_logger.addHandler(
        logging.FileHandler(os.path.join(results["output_path"], "results.log"), mode="w")
    )

    _log.info("Starting experiment at {}".format(timestamp))

    paths = pickle.load(open(detector["model_abs"], "rb"))
    mom_3 = pathpy.MultiOrderModel(paths, max_order=3)

    runs = get_runs(data["runs"], False)

    for scenario in runs:

        likelihoods = trial_scenario(mom_3, scenario["scenario_name"], 10, 2000000)
        for likelihood in likelihoods:
            _run.log_scalar("likelihood", likelihood[0], likelihood[1])

    ex.add_artifact(os.path.join(results["output_path"], "results.log"))
