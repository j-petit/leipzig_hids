import argparse
import logging
import logging.config
import yaml

from src.run_experiment import ex
from src.preprocess_experiment import get_dataset
from src.preprocess_experiment import preprocess

import src.preprocess_experiment

from src.utils import load_config


if __name__ == "__main__":

    logging.config.fileConfig("config/logging_local.conf")
    logger = logging.getLogger("run")
    parser = argparse.ArgumentParser(description="Run components of the model source code")
    subparsers = parser.add_subparsers()

    # data subparser
    sb_data = subparsers.add_parser("get_data", description="Downloads the raw data")
    sb_data.add_argument("--config", default="config/config.yaml", help="Config file")
    sb_data.add_argument('args', nargs=argparse.REMAINDER)
    sb_data.set_defaults(func=src.preprocess_experiment.ex.run_commandline)
    sb_data.set_defaults(exp=src.preprocess_experiment.ex)
    sb_data.set_defaults(command="get_dataset")

    # preprocess subparser
    sb_preprocess = subparsers.add_parser("preprocess_data", description="Preprocesses raw data")
    sb_preprocess.add_argument("--config", default="config/config.yaml", help="Config file")
    sb_preprocess.add_argument('args', nargs=argparse.REMAINDER)
    sb_preprocess.set_defaults(func=src.preprocess_experiment.ex.run_commandline)
    sb_preprocess.set_defaults(exp=src.preprocess_experiment.ex)
    sb_preprocess.set_defaults(command="preprocess")

    # train subparser
    sb_train = subparsers.add_parser("train_model", description="Train model")
    sb_train.add_argument("--config", default="config/config.yaml", help="Config file")
    sb_train.add_argument('args', nargs=argparse.REMAINDER)
    sb_train.set_defaults(func=ex.run_commandline)
    sb_train.set_defaults(exp=ex)
    sb_train.set_defaults(command="my_main")

    args = parser.parse_args()

    print(args)

    config = load_config(args.config)
    args.exp.add_config(config)
    args.args = [''] + [args.command] + args.args

    print(args)

    args.exp.run_commandline(args.args)

