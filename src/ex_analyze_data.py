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
import numpy as np
from matplotlib import pyplot as plt
from scipy import stats

import sacred

from src.data_processing import generate_temporal_network, get_runs
from src.preprocess_experiment import create_train_test_split
from src.utils import config_adapt


def analyze(config):
    def report(i):
        i % 10 == 0 and print(f"Processed {i} logs of {total}")

    logger = logging.getLogger("hids.analyze")

    train, _ = create_train_test_split(config["data"]["runs"], config["model"]["train_examples"])
    runs = get_runs(config["data"]["runs"], train)

    total = len(runs)

    normal_graphs = [
        report(i) or generate_temporal_network(scenario, None)
        for i, scenario in enumerate(runs["path"])
    ]

    save_path = os.path.join(config["analyze"]["figures"], f'{config["dataset"]}_time_analyze.png')

    inter_event_times_all = analyze_time(normal_graphs, save_path)

    statistics = stats.describe(inter_event_times_all)

    logger.debug("runs for training")
    logger.debug(runs)

    logger.info("Summary time statistics")
    logger.info("")
    logger.info(statistics)


def analyze_time(temporal_nets, save_path=None):

    multi = [x.inter_event_times().flatten() for x in temporal_nets]
    means = [x.mean() / 1000.0 for x in multi]
    max_times = [x.max() / 1000000.0 for x in multi]
    multi = np.concatenate(multi)

    observation_lengths = [x.observation_length() for x in temporal_nets]

    plt.tight_layout()
    # these are my measurements, unsorted
    fig = plt.figure(figsize=(8, 20))
    fig.subplots_adjust(hspace=0.3)

    plt.subplot(411)
    plt.hist(
        multi,
        bins=np.logspace(np.log10(1), np.log10(np.percentile(multi, 99)), 50),
        weights=100 * np.ones(len(multi)) / len(multi),
        color="blue",
        edgecolor="black",
        alpha=0.5,
        range=(0, np.percentile(multi, 99)),
    )
    plt.gca().set_xscale("log")
    plt.title("Histogram Time Differences (Log)")
    plt.xlabel("Time differences [$\mu s$]")
    plt.ylabel("Percentage [%]")

    plt.subplot(412)
    plt.hist(
        multi,
        bins=50,
        weights=100 * np.ones(len(multi)) / len(multi),
        color="blue",
        edgecolor="black",
        alpha=0.5,
        range=(0, np.percentile(multi, 90)),
    )
    plt.title("Histogram Time Differences of 90 percentile")
    plt.xlabel("Time differences [$\mu s$]")
    plt.ylabel("Percentage [%]")

    plt.subplot(413)
    plt.hist(
        means,
        bins=50,
        weights=100 * np.ones(len(means)) / len(means),
        color="blue",
        edgecolor="black",
        alpha=0.5,
        range=(0, np.percentile(means, 99)),
    )
    plt.title("Histogram Mean Time Difference")
    plt.xlabel("Mean time differences [ms]")
    plt.ylabel("Percentage [%]")

    plt.subplot(414)
    plt.hist(
        max_times,
        bins=50,
        weights=100 * np.ones(len(means)) / len(means),
        color="blue",
        edgecolor="black",
        alpha=0.5,
        range=(0, np.percentile(max_times, 99)),
    )
    plt.title("Histogram Maximum Time Difference")
    plt.xlabel("Maximum time differences [s]")
    plt.ylabel("Percentage [%]")

    if save_path:
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        plt.savefig(save_path, bbox_inches="tight")

    return multi
