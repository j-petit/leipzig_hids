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
import multiprocessing

import sacred

from src.data_processing import process_raw_temporal_dataset, get_runs
from src.preprocess_experiment import create_train_test_split
from src.attack_simulate import trial_scenario
from src.scenario_analyzer import ScenarioAnalyzer
from src.utils import config_adapt


def create_model(config, sacred_run):

    model = config["model"]
    data = config["data"]
    simulate = config["simulate"]

    logger = logging.getLogger("hids.preprocess")

    paths = pickle.load(open(model["paths"], "rb"))


    logger.info(paths)
    logger.info("Creating multi order model now...")

    mom = pathpy.MultiOrderModel(paths, max_order=model["max_order"], prior=model["prior"])
    order = mom.estimate_order()
    mom = pathpy.MultiOrderModel(paths, max_order=order, prior=model["prior"], unknown=model["unknown"])

    if not os.path.exists(os.path.dirname(model["save"])):
        os.makedirs(os.path.dirname(model["save"]))

    pickle.dump(mom, open(model["save"], "wb"))

    logger.info(mom)

    logger.info("Now computing the likelihood threshold...")

    train, _ = create_train_test_split(data["runs"], model["train_examples"])
    runs = get_runs(data["runs"], train)

    run_paths = list(runs["path"])
    moms = [mom] * len(run_paths)
    dts = [model["time_delta"]] * len(run_paths)
    time_windows = [simulate["time_window"]] * len(run_paths)

    ins = zip(moms, run_paths, dts, time_windows)

    with multiprocessing.Pool(simulate["cpu_count"]) as pool:
        results = pool.starmap(trial_scenario, ins)

    #results = []
    #for in_params in ins:
    #    results.append(trial_scenario(*in_params))

    analyzer = ScenarioAnalyzer(simulate["threshold"], sacred_run, runs)

    for result in results:
        analyzer.add_run(result)

    df = analyzer.evaluate_runs()
    min_likelihood = analyzer.get_min_likelihood(0.2)

    logger.info("\n %s", str(df))

    analyzer.write_misclassified_runs(only_wrong=False)

    logger.info("The mimimum likelihood in the training set is %s.", min_likelihood)

    return min_likelihood
