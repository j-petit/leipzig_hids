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

import sacred

from src.data_processing import process_raw_temporal_dataset, get_runs
from src.utils import config_adapt


def create_model(config):

    model = config["model"]

    results_logger = logging.getLogger("ex_create_model")
    log_file = os.path.join(config["c_results"]["output_path"], "ex_create_model.log")
    hdlr = logging.FileHandler(log_file, mode="w")
    results_logger.addHandler(hdlr)

    paths = pickle.load(open(model["paths"], "rb"))

    results_logger.info(paths)
    results_logger.info("Creating multi order model now...")

    mom = pathpy.MultiOrderModel(paths, max_order=model["max_order"], prior=model["prior"])
    order = mom.estimate_order()
    mom = pathpy.MultiOrderModel(paths, max_order=order, prior=model["prior"], unknown=True)

    if not os.path.exists(os.path.dirname(model["save"])):
        os.makedirs(os.path.dirname(model["save"]))

    pickle.dump(mom, open(model["save"], "wb"))

    results_logger.info(mom)
