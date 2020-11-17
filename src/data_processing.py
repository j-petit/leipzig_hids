"""
File: data_processing.py
Author: Jens Petit
Email: petit@informatik.uni-leipzig.de
"""

import os
import sys
import operator
from functools import reduce
from collections import Counter

import yaml
import pandas as pd
import numpy as np
from datetime import datetime
import pudb
import pathpy


def process_raw_temporal_dataset(runs, time_delta, syscalls_ids=None):
    """Generates pathpy ready dataset out of raw data

    Parameters
    ----------
    runs : pandas.dataframe
        Content of runs.csv file
    time_delta : int
        Indicates the time-difference threshold for generating a valid path
    syscalls : bidict
        Bidirectional dictionary specifying the mapping between integers and syscall

    Returns
    -------
    data : pathpy.path
    """

    total = len(runs)

    def report(i):
        i % 10 == 0 and print(f"Processed {i} logs of {total}")

    normal_graphs = [
        report(i) or generate_temporal_network(scenario, syscalls_ids)
        for i, scenario in enumerate(runs["path"])
    ]

    print(f"Extracting temporal valid paths with time_delta {time_delta} out of {total} runs.")

    paths = [
        pathpy.path_extraction.paths_from_temporal_network_single(
            net, delta=time_delta, max_subpath_length=3
        )
        for net in normal_graphs
    ]

    return reduce(operator.add, paths)


def get_runs(path: str, selector=None):

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


def generate_temporal_network(path: str, syscalls_ids=None):
    """Temporal network with pathpy

    Parameters
    ----------
    path : str
        The log-file
    syscalls_ids : bidict.bidict
        Mapping between syscalls and integers

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
