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

from src.data_processing import process_raw_temporal_dataset


def preprocess(args):

    with open(args.config, "r") as config_file:
        config = yaml.safe_load(config_file)

    dataset_runs = os.path.join(
        config["data"]["prefix"], config["data"]["name"], config["data"]["runs"]
    )

    time_delta = config["features"]["time_delta"]

    paths = process_raw_temporal_dataset(dataset_runs, time_delta)

    pickle.dump(
        paths, open(os.path.join(config["data"]["prefix"], f"temp_paths_{time_delta}.p"), "wb"),
    )

    print(paths)

    mog = pathpy.MultiOrderModel(paths, max_order=7)
    order = mog.estimate_order()

    hon = pathpy.HigherOrderNetwork(paths, k=order)

    print(hon)

    pickle.dump(
        hon,
        open(os.path.join(config["data"]["prefix"], f"hon_{order}_delta_{time_delta}.p"), "wb"),
    )


def get_dataset(args):
    """Downloads the dataset if it is not yet available and unzips it"""

    datasets = {
        "CVE-2017-7529": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/CVE-2017-7529.tar.gz"
    }

    with open(args.config, "r") as config_file:
        config = yaml.load(config_file)

    if not os.path.exists(args.data_prefix):
        os.system(f"mkdir {args.data_prefix}")

    try:
        link = datasets[config["data"]["name"]]
    except KeyError as key:
        print("This dataset does not exist. Aborting.")
        print(f"The key was {key}")
        sys.exit(1)

    datapath = f"{args.data_prefix}/{args.name}.tar.gz"

    print(datapath)

    if not os.path.exists(datapath):
        os.system(f"curl -LOJ {link}")
        os.system(f"mv {args.name}.tar.gz {datapath}")
        os.system(f"tar -zxvf {datapath} -C {args.data_prefix}/")
