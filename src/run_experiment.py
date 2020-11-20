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
from tqdm import tqdm

from src.attack_simulate import trial_scenario
from src.preprocess_experiment import create_train_test_split
from src.data_processing import generate_temporal_network, get_runs
from src.scenario_analyzer import ScenarioAnalyzer
from src.utils import config_adapt

import src.istarmap


def my_main(config, sacred_run, min_likelihood=None):
    """Simulates runs with a trained model.

    Parameters
    ----------
    config : dict
        main config dictionary
    sacred_run : sacred.run
        to store metrics
    min_likelihood : float
        likelihood threshold to detect attacks
    """

    model = config["model"]
    simulate = config["simulate"]
    data = config["data"]

    results_logger = logging.getLogger("hids.results")

    mom = pickle.load(open(model["save"], "rb"))

    _, test = create_train_test_split(data["runs"], model["train_examples"])

    runs = get_runs(data["runs"], test)

    if simulate["list_attacks"]:
        runs = runs[runs["scenario_name"].isin(simulate["list_attacks"])]
    else:
        try:
            norm_samples = runs[runs["is_executing_exploit"] == False].sample(
                simulate["normal_samples"]
            )
        except ValueError:
            norm_samples = runs[runs["is_executing_exploit"] == False]
        try:
            attack_samples = runs[runs["is_executing_exploit"]].sample(simulate["attack_samples"])
        except ValueError:
            attack_samples = runs[runs["is_executing_exploit"]]
        runs = pd.concat([norm_samples, attack_samples])

    run_paths = list(runs["path"])
    moms = [mom] * len(run_paths)
    dts = [model["time_delta"]] * len(run_paths)
    time_windows = [simulate["time_window"]] * len(run_paths)

    ins = list(zip(moms, run_paths, dts, time_windows))

    results_logger.info("test")

    results = []
    with multiprocessing.Pool(simulate["cpu_count"]) as pool:
        for result in tqdm(pool.istarmap(trial_scenario, ins), total=len(ins)):
            results.append(result)


    results_logger.info("done with trials")


    # for in_params in ins:
    #    results.append(trial_scenario(*in_params))

    if min_likelihood:
        analyzer = ScenarioAnalyzer(min_likelihood, sacred_run, runs)
    else:
        analyzer = ScenarioAnalyzer(simulate["threshold"], sacred_run, runs)

    results_logger.debug("Using likelihood threshold of %s", analyzer.threshold)

    for run_result in results:
        analyzer.add_run(run_result)

    df = analyzer.evaluate_runs()
    report = analyzer.get_report()
    results_logger.info(report)
    results_logger.info("\n %s", str(df))

    df.to_csv(os.path.join(config["c_results"]["output_path"], "results.csv"))

    analyzer.write_misclassified_runs(only_wrong=False)

    # pickle.dump(analyzer, open(os.path.join(results["output_path"], "analyzer.p"), "wb"))
