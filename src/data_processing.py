"""
File: data_processing.py
Author: Jens Petit
Email: petit@informatik.uni-leipzig.de
"""

import os
import sys
import operator
import subprocess
from functools import reduce
from collections import Counter

import yaml
import pandas as pd
import numpy as np
from datetime import datetime
import pudb
import pathpy
import logging


def process_raw_temporal_dataset(runs, time_delta):
    """Generates pathpy ready dataset out of raw data

    Parameters
    ----------
    runs : pandas.dataframe
        Content of runs.csv file
    time_delta : int
        Indicates the time-difference threshold for generating a valid path. If time_delta is zero,
        the thread information will be used to split the paths.

    Returns
    -------
    data : pathpy.path
    """

    total = len(runs)

    def report(i):
        i % 10 == 0 and print(f"Processed {i} logs of {total}")

    if time_delta != 0:

        normal_graphs = [
            report(i) or generate_temporal_network(scenario)
            for i, scenario in enumerate(runs["path"])
        ]
        print(f"Extracting temporal valid paths with time_delta {time_delta} out of {total} runs.")
        paths = [
            pathpy.path_extraction.paths_from_temporal_network_single(
                net, delta=time_delta, max_subpath_length=3
            )
            for net in normal_graphs
        ]

    else:
        print(f"Time delta was 0, therefore using thread info to extract valid paths.")
        paths = [
            report(i) or generate_paths_from_threads(parse_run_to_pandas(run))
            for i, run in enumerate(runs["path"])
        ]

    return reduce(operator.add, paths)


def get_runs(path: str, selector=None):
    """Returns the information of all runs in a single scenario.

    Parameters
    ----------
    path: string
        The path to the runs.csv file

    Returns
    -------
    runs : pandas.dataframe
    """

    runs = pd.read_csv(path, skipinitialspace=True)

    if selector is not None:
        runs = runs.loc[selector]

    scenario_file = lambda x: os.path.join(os.path.dirname(path), x + ".txt")

    runs["path"] = runs["scenario_name"].apply(scenario_file)

    return runs


def parse_syscall(syscall):
    """Creates list of infos contained in a syscall

    # syscall entries:
    # 0 - event_number
    # 1 - event_time
    # 2 - cpu
    # 3 - user_uid
    # 4 - process_name
    # 5 - thread_id
    # 6 - event_direction: > start syscall with with params listed below < return
    # 7 - event_type
    # 8 - event_arguments

    Parameters
    ----------
    syscall : str
        The raw string containing the syscall info

    Returns
    -------
    parsed_syscall : list of str
    """

    syscall = syscall.split()
    parsed_syscall = []
    parsed_syscall[0:8] = syscall[0:8]
    list_of_arguments = syscall[8:]
    parsed_syscall.append(list_of_arguments)
    return parsed_syscall


def generate_temporal_network(path: str):
    """Temporal network with pathpy

    Parameters
    ----------
    path : str
        The log-file

    Returns
    -------
    pathpy.TemporalNetwork

    """

    format_string = "%H:%M:%S.%f"

    def parse_timestamps(time: str):
        return datetime.strptime(time[:-3], format_string)

    def normalize_time(time):
        return round((time - start_time).total_seconds() * 1000000)

    with open(path) as raw_file:
        syscalls = raw_file.readlines()

    syscalls = [parse_syscall(syscall.strip()) for syscall in syscalls]
    syscalls = [syscall for syscall in syscalls if syscall[6] == "<"]

    event_types = [syscall[7] for syscall in syscalls]

    timestamps = [parse_timestamps(syscall[1]) for syscall in syscalls]
    start_time = timestamps[0]

    timestamps = [normalize_time(time) for time in timestamps]

    transitions = list(zip(event_types, event_types[1:], timestamps))

    return pathpy.TemporalNetwork(transitions)


def generate_paths_from_threads(run_data, start_end_time=None):
    """Uses the thread information to create paths. Each unique thread creates a path.

    Parameters
    ----------
    run_data : pandas.Dataframe
        single run log
    start_end_time: pair(int, int)
        if specified defines the time window

    Returns
    -------
    paths : pathpy.Paths
        extracted paths
    """

    paths = pathpy.Paths()
    paths.max_subpath_length = 4

    if start_end_time is not None:
        run_data = run_data.loc[
            (run_data["time"] >= start_end_time[0]) & (run_data["time"] < start_end_time[1])
        ]

    for _, thread_data in run_data.groupby("thread_id"):
        paths.add_path(thread_data["syscall"].to_list())

    return paths


def parse_run_to_pandas(run_file: str):
    """Extracts the data from a single run.

    Parameters
    ----------
    run_file : str
        path to the file

    Returns
    -------
    run_data : pandas.Dataframe
    """

    logger = logging.getLogger("hids.preprocess")
    logger.debug("Currently working on %s", run_file)

    parser = lambda time_str: datetime.strptime(time_str[:-3], "%H:%M:%S.%f")

    run_data = pd.read_csv(
        run_file,
        delim_whitespace=True,
        usecols=[1, 5, 6, 7],
        names=["time", "thread_id", "dir", "syscall"],
        parse_dates=["time"],
        date_parser=parser,
        quoting=3,
    )

    run_data = run_data[run_data["dir"] == "<"]
    run_data = run_data.drop("dir", axis=1)

    run_data.reset_index()

    # convert datetime to microseconds
    run_data["time"] -= run_data["time"].iat[0]
    run_data["time"] = run_data["time"].apply(
        lambda my_time: round(my_time.total_seconds() * 1000000)
    )

    return run_data
