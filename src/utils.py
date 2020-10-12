import bidict
import yaml
import os
from datetime import datetime
import pandas as pd
import pathpy
import multiprocessing


def load_config(config: str):
    """Custom function to load a config file with additional constructor

    Parameters
    ----------
    config : str
        Path to the config.yaml file

    Returns
    -------
    config : dict
    """

    def join(loader, node):
        seq = loader.construct_sequence(node)
        return "/".join([str(i) for i in seq])

    yaml.add_constructor("!join", join)
    with open(config, "r") as config_file:
        config = yaml.load(config_file, yaml.FullLoader)

    return config


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


def create_null_paths(model):
    def nesting_loop(to_iterate):

        result = []

        for i in to_iterate:
            for j in to_iterate:
                result.append((i, j))

        return result

    max_order = model.max_order
    nodes = model.paths.nodes

    for _ in range(2):
        nodes = nesting_loop(nodes)

    return nodes


def config_adapt(config):

    my_config = yaml.load(open("config/config.yaml", "r"), Loader=yaml.SafeLoader)

    pd.set_option("display.max_columns", 500)
    pd.set_option("display.max_rows", None)
    pd.options.display.width = 0
    log = pathpy.utils.Log
    log.set_min_severity(my_config["pathpy"]["min_severity"])

    my_config["data"]["raw"] = os.path.join(my_config["data"]["prefix"], "raw")
    my_config["data"]["processed"] = os.path.join(my_config["data"]["prefix"], "processed")
    my_config["data"]["interim"] = os.path.join(my_config["data"]["prefix"], "interim")

    my_config["data"]["runs"] = os.path.join(
        my_config["data"]["raw"], my_config["dataset"], "runs.csv"
    )
    my_config["data"]["scenarios"] = os.path.join(my_config["data"]["raw"], my_config["dataset"])

    my_config["timestamp"] = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    my_config["simulate"]["cpu_count"] = multiprocessing.cpu_count()

    my_config["model"]["paths"] = os.path.join(
        my_config["data"]["processed"], f'temp_paths_{my_config["model"]["time_delta"]}.p'
    )
    my_config["model"]["save"] = os.path.join(
        my_config["model"]["prefix"],
        my_config["dataset"],
        f'MOM_delta_{my_config["model"]["time_delta"]}_prior_{my_config["model"]["prior"]}.p',
    )

    my_config["c_results"]["output_path"] = os.path.join(
        my_config["c_results"]["prefix"], my_config["dataset"], my_config["timestamp"]
    )

    if not os.path.exists(my_config["c_results"]["output_path"]):
        os.makedirs(my_config["c_results"]["output_path"])

    return my_config
