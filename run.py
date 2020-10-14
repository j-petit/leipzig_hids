import logging
import logging.config
import yaml
import sacred
import pprint
import os
from datetime import datetime
import dotenv
import multiprocessing
import pandas as pd
import pathpy

from sacred import Experiment
from sacred.observers import MongoObserver

from src.utils import config_adapt
import src.get_data, src.preprocess_experiment, src.run_experiment, src.ex_create_model, src.ex_analyze_data


ex = sacred.Experiment('hids')
ex.add_config(yaml.load("config/config.yaml", yaml.SafeLoader))


dotenv.load_dotenv(".env")
URI = "mongodb://{}:{}@139.18.13.64/?authSource=hids&authMechanism=SCRAM-SHA-1".format(
    os.environ["SACRED_MONGODB_USER"], os.environ["SACRED_MONGODB_PWD"]
)
ex.observers.append(MongoObserver(url=URI, db_name="hids"))


@ex.command(unobserved=True)
def print_config(_config):
    """ Replaces print_config which is not working with python 3.8 and current packages sacred"""
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(_config)


@ex.config
def config(data, dataset, c_results, model, simulate):

    data["raw"] = os.path.join(data["prefix"], "raw")
    data["processed"] = os.path.join(data["prefix"], "processed")
    data["interim"] = os.path.join(data["prefix"], "interim")

    data["runs"] = os.path.join(
        data["raw"], dataset, "runs.csv"
    )
    data["scenarios"] = os.path.join(data["raw"], dataset)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    simulate["cpu_count"] = multiprocessing.cpu_count()

    model["paths"] = os.path.join(
        data["processed"], f'temp_paths_{model["time_delta"]}.p'
    )
    model["save"] = os.path.join(
        model["prefix"],
        dataset,
        f'MOM_delta_{model["time_delta"]}_prior_{model["prior"]}.p',
    )

    c_results["output_path"] = os.path.join(
        c_results["prefix"], dataset, timestamp
    )


@ex.config_hook
def hook(config, command_name, logger):

    config.update({'hook': True})

    pd.set_option("display.max_columns", 500)
    pd.set_option("display.max_rows", None)
    pd.options.display.width = 0
    pathpy.utils.Log.set_min_severity(config["pathpy"]["min_severity"])

    if not os.path.exists(config["c_results"]["output_path"]):
        os.makedirs(config["c_results"]["output_path"])

    logging.config.fileConfig("config/logging_local.conf")

    return config


@ex.automain
def run(hook, _config, stages, c_results, _run):

    if stages["pull_data"]:
        src.get_data.get_dataset(_config)
    if stages["analyze"]:
        src.ex_analyze_data.analyze(_config)
        ex.add_artifact(os.path.join(c_results["output_path"], "ex_analyze_data.log"))
    if stages["make_temp_paths"]:
        src.preprocess_experiment.preprocess(_config)
        ex.add_artifact(os.path.join(c_results["output_path"], "ex_make_temp_paths.log"))
    if stages["create_model"]:
        src.ex_create_model.create_model(_config)
        ex.add_artifact(os.path.join(c_results["output_path"], "ex_create_model.log"))
    if stages["simulate"]:
        src.run_experiment.my_main(_config, _run)
        ex.add_artifact(os.path.join(c_results["output_path"], "results.log"))
        ex.add_artifact(os.path.join(c_results["output_path"], "results.csv"))
