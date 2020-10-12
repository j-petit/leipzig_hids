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
from src.utils import config_adapt


def my_main(config, run):

    model = config["model"]
    simulate = config["simulate"]
    data = config["data"]

    logger = logging.getLogger("main")
    log_file = os.path.join(config["c_results"]["output_path"], "general.log")
    hdlr = logging.FileHandler(log_file, mode="w")
    hdlr.setFormatter(logging.Formatter(fmt="%(asctime)s %(name)-12s %(levelname)-8s %(message)s"))
    logger.addHandler(hdlr)

    results_logger = logging.getLogger("results")
    results_logger.addHandler(
        logging.FileHandler(os.path.join(config["c_results"]["output_path"], "results.log"), mode="w")
    )

    analyzer = ScenarioAnalyzer(simulate["threshold"], run)

    mom = pickle.load(open(model["save"], "rb"))

    train, test = create_train_test_split(data["runs"], model["train_examples"])

    runs = get_runs(data["runs"], test)

    if simulate["list_attacks"]:
        runs = runs[runs["scenario_name"].isin(simulate["list_attacks"])]
    else:
        runs = pd.concat(
            [
                runs[runs["is_executing_exploit"] == False].sample(simulate["normal_samples"]),
                runs[runs["is_executing_exploit"] == True].sample(simulate["attack_samples"]),
            ]
        )

    run_paths = list(runs["path"])
    moms = [mom] * len(run_paths)
    dts = [model["time_delta"]] * len(run_paths)
    time_windows = [2000000] * len(run_paths)

    ins = zip(moms, run_paths, dts, time_windows)

    with multiprocessing.Pool(simulate["cpu_count"]) as pool:
        results = pool.starmap(trial_scenario, ins)

    #results = trial_scenario(*next(ins))
    #results = [results]

    for i, scenario_result in enumerate(results):
        analyzer.add_run(scenario_result, runs.iloc[i])

    report, df = analyzer.evaluate_runs()
    results_logger.info(report)
    results_logger.info("\n" + str(df))

    df.to_csv(os.path.join(config["c_results"]["output_path"], "results.csv"))

    analyzer.write_misclassified_runs(only_wrong=False)

    # pickle.dump(analyzer, open(os.path.join(results["output_path"], "analyzer.p"), "wb"))
