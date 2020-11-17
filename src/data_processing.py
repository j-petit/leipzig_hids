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
            report(i) or generate_paths_from_threads(run) for i, run in enumerate(runs["path"])
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


def generate_paths_from_threads(run_file: str):
    """Uses the thread information to create paths. Each unique thread creates a path.

    Parameters
    ----------
    run_file : string
        single run log

    Returns
    -------
    paths : pathpy.Paths
        extracted paths
    """

    result = subprocess.run(
        ["sort", "-t ", "-k6,6n", "-k1,1n", run_file], capture_output=True, text=True, check=True
    )

    syscalls = result.stdout.splitlines()
    syscalls = [parse_syscall(syscall.strip()) for syscall in syscalls]
    syscalls = [syscall for syscall in syscalls if syscall[6] == "<"]
    event_types = [syscall[7] for syscall in syscalls]

    thread_ids = np.array([syscall[5] for syscall in syscalls])
    _, idx_unique_threads = np.unique(thread_ids, return_index=True)
    idx_unique_threads = np.append(idx_unique_threads, len(thread_ids))

    paths = pathpy.Paths()
    paths.max_subpath_length = 4

    for idx_thread in zip(idx_unique_threads, idx_unique_threads[1:]):
        if (idx_thread[1] - idx_thread[0]) > 1:
            paths.add_path(event_types[idx_thread[0]:idx_thread[1]])

    return paths
