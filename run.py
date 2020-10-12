import logging
import logging.config
import yaml
import sacred
import pprint
import os
from datetime import datetime
import dotenv

from sacred import Experiment
from sacred.observers import MongoObserver

from src.utils import config_adapt
import src.get_data, src.preprocess_experiment, src.run_experiment, src.ex_create_model, src.ex_analyze_data


ex = sacred.Experiment('hids_main', ingredients=[src.get_data.ex, src.preprocess_experiment.ex, src.ex_create_model.ex, src.run_experiment.ex, src.ex_analyze_data.ex])


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


@ex.config_hook
def hook(config, command_name, logger):
    config = config_adapt(config)
    config.update({'hook': True})
    return config


@ex.automain
def run(hook, stages, c_results):
    logging.config.fileConfig("config/logging_local.conf")
    logger = logging.getLogger("run")

    if (stages["pull_data"]):
        src.get_data.get_dataset()
    if (stages["analyze"]):
        src.ex_analyze_data.analyze()
        ex.add_artifact(os.path.join(c_results["output_path"], "ex_analyze_data.log"))
    if (stages["make_temp_paths"]):
        src.preprocess_experiment.preprocess()
        ex.add_artifact(os.path.join(c_results["output_path"], "ex_make_temp_paths.log"))
    if (stages["create_model"]):
        src.ex_create_model.create_model()
        ex.add_artifact(os.path.join(c_results["output_path"], "ex_create_model.log"))
    if (stages["simulate"]):
        src.run_experiment.my_main()
        ex.add_artifact(os.path.join(c_results["output_path"], "results.log"))
        ex.add_artifact(os.path.join(c_results["output_path"], "results.csv"))
