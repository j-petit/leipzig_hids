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
from src.utils import load_config


project_dir = os.path.join(os.path.dirname(__file__), os.pardir)
dotenv_path = os.path.join(project_dir, ".env")
dotenv.load_dotenv(dotenv_path)

URI = "mongodb://{}:{}@139.18.13.64/?authSource=hids&authMechanism=SCRAM-SHA-1".format(
    os.environ["SACRED_MONGODB_USER"], os.environ["SACRED_MONGODB_PWD"]
)

ex = sacred.Experiment("hids_create_model")
ex.observers.append(sacred.observers.MongoObserver(url=URI, db_name="hids"))


@ex.command(unobserved=True)
def print_config(_config):
    """ Replaces print_config which is not working with python 3.8 and current packages sacred"""
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(_config)


@ex.automain
def create_model(_log, model, c_results):

    results_logger = logging.getLogger("ex_create_model")
    log_file = os.path.join(c_results["output_path"], "ex_create_model.log")
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
