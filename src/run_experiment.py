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
from src.preprocess_experiment import create_train_test_split
from src.data_processing import generate_temporal_network, get_runs
from src.scenario_analyzer import ScenarioAnalyzer
from src.utils import load_config


project_dir = os.path.join(os.path.dirname(__file__), os.pardir)
dotenv_path = os.path.join(project_dir, ".env")
dotenv.load_dotenv(dotenv_path)

URI = "mongodb://{}:{}@139.18.13.64/?authSource=hids&authMechanism=SCRAM-SHA-1".format(
    os.environ["SACRED_MONGODB_USER"], os.environ["SACRED_MONGODB_PWD"]
)

ex = Experiment("hids")
ex.observers.append(MongoObserver(url=URI, db_name="hids"))
ex.logger = logging.getLogger("hids")
config = load_config("config/config.yaml")
ex.add_config(config)


@ex.config
def my_config(data, results, seed, dataset):

    if results["timestamp"]:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        experiment_name = "{}_{}".format(dataset.upper(), timestamp)
    else:
        experiment_name = "{}".format(dataset.upper())

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
        simulate,
        results,
        timestamp,
        model,
        data
):

    results_logger = logging.getLogger("results")
    results_logger.addHandler(
        logging.FileHandler(os.path.join(results["output_path"], "results.log"), mode="w")
    )

    _log.info("Starting experiment at {}".format(timestamp))

    analyzer = ScenarioAnalyzer(simulate["threshold"], _run)

    mom_3 = pickle.load(open(simulate["model"], "rb"))

    train, test = create_train_test_split(config["data"]["runs"], config["model"]["train_examples"])

    runs = get_runs(data["runs"], test)
    runs = pd.concat([runs[runs["is_executing_exploit"] == False],
                     runs[runs["is_executing_exploit"] == True].sample(simulate["attack_samples"])])

    for _, run in runs.iterrows():

        scenario_name = run["scenario_name"]

        results_logger.info(f"Starting simulation with {scenario_name}")
        results_logger.info("Is this exploit?:" + str(run["is_executing_exploit"]))

        scenario_results = trial_scenario(mom_3, run["path"], model["time_delta"], 2000000)

        analyzer.add_run(scenario_results, run)

    report, df = analyzer.evaluate_runs()
    analyzer.write_misclassified_runs()
    results_logger.info(report)
    results_logger.info(df)

    ex.add_artifact(os.path.join(results["output_path"], "results.log"))

    #pickle.dump(analyzer, open(os.path.join(results["output_path"], "analyzer.p"), "wb"))
