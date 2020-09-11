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
import multiprocessing

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


log = pathpy.utils.Log
log.set_min_severity(config['pathpy']['min_severity'])
pd.set_option('display.max_columns', 500)
pd.set_option('display.max_rows', None)
pd.options.display.width = 0

@ex.config
def my_config(data, simulate, c_results, seed, dataset):

    if c_results["timestamp"]:
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        experiment_name = "{}_{}".format(dataset.upper(), timestamp)
    else:
        experiment_name = "{}".format(dataset.upper())

    c_results["output_path"] = os.path.join(c_results["prefix"], experiment_name)
    os.makedirs(c_results["output_path"], exist_ok=True)

    log_file = os.path.join(c_results["output_path"], "general.log")
    hdlr = logging.FileHandler(log_file, mode="w")
    hdlr.setFormatter(logging.Formatter(fmt="%(asctime)s %(name)-12s %(levelname)-8s %(message)s"))
    ex.logger.addHandler(hdlr)

    simulate["cpu_count"] = multiprocessing.cpu_count()


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
        c_results,
        timestamp,
        model,
        data
):

    results_logger = logging.getLogger("results")
    results_logger.addHandler(
        logging.FileHandler(os.path.join(c_results["output_path"], "results.log"), mode="w")
    )

    _log.info("Starting experiment at {}".format(timestamp))

    analyzer = ScenarioAnalyzer(simulate["threshold"], _run)

    mom_3 = pickle.load(open(simulate["model"], "rb"))

    train, test = create_train_test_split(config["data"]["runs"], config["model"]["train_examples"])

    runs = get_runs(data["runs"], test)
    runs = pd.concat([runs[runs["is_executing_exploit"] == False].sample(simulate["normal_samples"]),
                     runs[runs["is_executing_exploit"] == True].sample(simulate["attack_samples"])])

    run_paths = list(runs["path"])
    moms = [mom_3] * len(run_paths)
    dts = [model["time_delta"]] * len(run_paths)
    time_windows = [2000000] * len(run_paths)

    ins = zip(moms, run_paths, dts, time_windows)

    with multiprocessing.Pool(simulate["cpu_count"]) as pool:
        results = pool.starmap(trial_scenario, ins)

    for i, scenario_result in enumerate(results):
        analyzer.add_run(scenario_result, runs.iloc[i])

    report, df = analyzer.evaluate_runs()
    results_logger.info(report)
    results_logger.info("\n" + str(df))

    df.to_csv(os.path.join(c_results["output_path"], "results.csv"))
    ex.add_artifact(os.path.join(c_results["output_path"], "results.log"))
    ex.add_artifact(os.path.join(c_results["output_path"], "results.csv"))

    analyzer.write_misclassified_runs()

    #pickle.dump(analyzer, open(os.path.join(results["output_path"], "analyzer.p"), "wb"))
