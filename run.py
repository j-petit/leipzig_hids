import argparse
import logging
import logging.config
import yaml

from src.run_experiment import ex
from src.preprocess_experiment import get_dataset
from src.preprocess_experiment import preprocess


if __name__ == "__main__":

    logging.config.fileConfig("config/logging_local.conf")
    logger = logging.getLogger("run")
    parser = argparse.ArgumentParser(description="Run components of the model source code")
    subparsers = parser.add_subparsers()

    # data subparser
    sb_data = subparsers.add_parser("get_data", description="Downloads the raw data")
    sb_data.add_argument("--config", default="config/config.yaml", help="Config file")
    sb_data.set_defaults(func=get_dataset)

    # preprocess subparser
    sb_preprocess = subparsers.add_parser("preprocess_data", description="Preprocesses raw data")
    sb_preprocess.add_argument("--config", default="config/config.yaml", help="Config file")
    sb_preprocess.set_defaults(func=preprocess)

    # train subparser
    sb_train = subparsers.add_parser("train_model", description="Train model")
    sb_train.add_argument("--config", default="config/config.yaml", help="Config file")
    sb_train.add_argument('args', nargs=argparse.REMAINDER)
    sb_train.set_defaults(func=ex.run)

    args = parser.parse_args()

    if args.func == ex.run:
        ex.add_config(args.config)
        sacred_args = [''] + args.args
        ex.run_commandline(sacred_args)
    else:
        args.func(args)
