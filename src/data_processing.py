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

import pandas as pd
import numpy as np
from torch_geometric.utils import from_scipy_sparse_matrix
from torch_geometric.data import Data
from scipy.sparse import coo_matrix
from sklearn.preprocessing import normalize
from datetime import datetime
import pudb
import bidict
import pathpy


datasets = {
    "CVE-2017-7529": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/CVE-2017-7529.tar.gz"
}


def get_dataset(name: str, data_prefix: str):
    """Downloads the dataset if it is not yet available

    Parameters
    ----------
    name : str
        Name of the dataset, will be checked against available
    data_prefix : str
        Prefix of the data directory
    """

    if not os.path.exists(data_prefix):
        os.system(f"mkdir {data_prefix}")

    try:
        link = datasets[name]
    except KeyError as key:
        print("This dataset does not exist. Aborting.")
        print(f"The key was {key}")
        sys.exit(1)

    datapath = f"{data_prefix}/{name}.tar.gz"

    print(datapath)

    if not os.path.exists(datapath):
        os.system(f"curl -LOJ {link}")
        os.system(f"mv {name}.tar.gz {datapath}")
        os.system(f"tar -zxvf {datapath} -C {data_prefix}/")


def process_raw_dataset(path: str, syscalls_ids=None):
    """Generates pytorch geometric ready dataset out of raw data

    Parameters
    ----------
    path : str
        Path to the runs.csv file
    syscalls : bidict
        Bidirectional dictionary specifying the mapping between integers and syscall

    Returns
    -------
    data : torch_geometric.data
    """

    def report(i):
        i % 10 == 0 and print(f"Processed {i} logs...")

    runs = pd.read_csv(path, skipinitialspace=True)

    normal_runs = runs[runs["is_executing_exploit"] == False]

    normal_graphs = [
        report(i)
        or generate_graph(os.path.join(os.path.dirname(path), scenario + ".txt"), syscalls_ids)
        for i, scenario in enumerate(normal_runs["scenario_name"])
    ]

    graph = reduce(operator.add, normal_graphs)

    adj = create_adjacency_matrix(graph)
    edge_index, edge_weight = from_scipy_sparse_matrix(adj)

    return Data(edge_index=edge_index, edge_attr=edge_weight)


def process_raw_temporal_dataset(path: str, time_delta, syscalls_ids=None):
    """Generates pathpy ready dataset out of raw data

    Parameters
    ----------
    path : str
        Path to the runs.csv file
    time_delta : int
        Indicates the time-difference threshold for generating a valid path
    syscalls : bidict
        Bidirectional dictionary specifying the mapping between integers and syscall

    Returns
    -------
    data : pathpy.path
    """

    def report(i):
        i % 10 == 0 and print(f"Processed {i} logs...")

    runs = pd.read_csv(path, skipinitialspace=True)

    normal_runs = runs[runs["is_executing_exploit"] == False]

    normal_graphs = [
        report(i)
        or generate_temporal_network(
            os.path.join(os.path.dirname(path), scenario + ".txt"), syscalls_ids
        )
        for i, scenario in enumerate(normal_runs["scenario_name"])
    ]

    paths = [
        pathpy.path_extraction.paths_from_temporal_network_single(net, delta=time_delta)
        for net in normal_graphs
    ]

    return reduce(operator.add, paths)


def create_adjacency_matrix(transition_counter):
    """Creates a row stochastic adjacency matrix out of Counter.

    Parameters
    ----------
    transition_counter : collections.Counter

    adj_size : int
        The size of the adjacency matrix

    Returns
    -------
    adj : scipy.sparse.coo_matrix
        Adjacency matrix

    """

    indices = list(transition_counter.keys())
    values = np.array(list(transition_counter.values()))

    rows = np.array([index[0] for index in indices])
    cols = np.array([index[1] for index in indices])

    adj = coo_matrix((values, (rows, cols)), dtype=float)
    return normalize(adj, norm="l1", axis=1)


def generate_graph(path: str, syscalls_ids=None):
    """Generates a graph out of a syscall file

    Parameters
    ----------
    path : str
        Path to the logfile
    syscalls :
        All available syscalls

    Returns
    -------
    data : torch_geometric.data
    """

    with open(path) as raw_file:
        syscalls = raw_file.readlines()

    syscalls = [parse_syscall(syscall.strip()) for syscall in syscalls]

    if syscalls_ids:
        try:
            event_types = [syscalls_ids[syscall[7]] for syscall in syscalls]
        except KeyError as key:
            print(f"The syscall {key} is not valid. Skipping experiment {path}")
            return Counter()
    else:
        event_types = [syscall[7] for syscall in syscalls]

    transitions = list(zip(event_types, event_types[1:]))

    transition_counts = Counter(transitions)

    return transition_counts


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


def create_bidict(path: str):
    """Creates bidict object for mapping between syscall and integer. The string is the key.

    Parameters
    ----------
    path : str
        Location of textfile with two columns

    Returns
    -------
    bidict.bidict
    """

    temp_dict = {}

    with open(path) as raw_file:
        syscalls = raw_file.readlines()

    for i, syscall in enumerate(syscalls):
        temp_dict[syscall.strip()] = i

    return bidict.bidict(temp_dict)


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
        return round((time - start_time).total_seconds() * 1000)

    with open(path) as raw_file:
        syscalls = raw_file.readlines()

    syscalls = [parse_syscall(syscall.strip()) for syscall in syscalls]

    event_types = [syscall[7] for syscall in syscalls]

    timestamps = [parse_timestamps(syscall[1]) for syscall in syscalls]
    start_time = timestamps[0]

    timestamps = [normalize_time(time) for time in timestamps]

    transitions = list(zip(event_types, event_types[1:], timestamps))

    return pathpy.TemporalNetwork(transitions)
