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
import pudb

import sacred

from src.data_processing import process_raw_temporal_dataset, get_runs
from src.utils import load_config

ex = sacred.Experiment("test")

@ex.command(unobserved=True)
def print_config(_config):
    """ Replaces print_config which is not working with python 3.8 and current packages sacred"""
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(_config)


@ex.command(unobserved=True)
def preprocess(_config):

    config = _config

    log = pathpy.utils.Log
    log.set_min_severity(config["pathpy"]["min_severity"])

    time_delta = config["model"]["time_delta"]

    intermediate_directory = config["data"]["processed"]

    os.makedirs(intermediate_directory, exist_ok=True)

    train, _ = create_train_test_split(config["data"]["runs"], config["model"]["train_examples"])

    runs = get_runs(config["data"]["runs"], train)

    paths = process_raw_temporal_dataset(runs, time_delta)

    pickle.dump(
        paths, open(os.path.join(intermediate_directory, f"temp_paths_{time_delta}.p"), "wb"),
    )

    print(paths)

    mom = pathpy.MultiOrderModel(paths, max_order=7)
    order = mom.estimate_order()
    mom = pathpy.MultiOrderModel(paths, max_order=order)

    os.makedirs(config["model"]["save"], exist_ok=True)

    pickle.dump(
        mom, open(os.path.join(config["model"]["save"], f"MOM_delta_{time_delta}.p"), "wb"),
    )


@ex.command(unobserved=True)
def get_dataset(_config):
    """Downloads the dataset if it is not yet available and unzips it"""

    print(_config)

    datasets = {
        "CVE-2014-0160": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/CVE-2014-0160.tar.gz",
        "CWE-434": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/PHP_CWE-434.tar.gz",
        "CWE-307": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/Bruteforce_CWE-307.tar.gz",
        "CWE-89": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/SQL_Injection_CWE-89.gz",
        "ZipSlip": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings/ZipSlip.tar.gz",
        "CVE-2012-2122": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/CVE-2012-2122.tar.gz",
        "CVE-2017-7529": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/CVE-2017-7529.tar.gz",
        "CVE-2018-3760": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/CVE-2018-3760.tar.gz",
        "CVE-2019-5418": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/CVE-2019-5418.tar.gz",
    }

    config = _config

    os.makedirs(config["data"]["raw"], exist_ok=True)

    try:
        link = datasets[config["dataset"]]
    except KeyError as key:
        print("This dataset does not exist. Aborting.")
        print(f"The key was {key}")
        sys.exit(1)

    datapath = "{}/{}.tar.gz".format(config["data"]["raw"], config["dataset"])

    print(datapath)

    if not os.path.exists(datapath):
        os.system(f"curl -LOJ {link}")
        os.system(f"mv {config['dataset']}.tar.gz {datapath}")
        os.system(f"tar -zxvf {datapath} -C {config['data']['raw']}")
        os.system(f"rm {datapath}")


def create_train_test_split(runs: str, num_train: int):

    all_runs = pd.read_csv(runs, skipinitialspace=True)
    train_runs = all_runs[all_runs["is_executing_exploit"] == False].head(num_train)
    train = train_runs.index
    test_runs = all_runs.loc[~all_runs.index.isin(train)]
    test = test_runs.index

    return train, test
