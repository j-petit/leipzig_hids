import argparse
import logging
import logging.config

from src.run_experiment import my_main


if __name__ == '__main__':

    logging.config.fileConfig("config/logging/local.conf")
    logger = logging.getLogger("run")
    parser = argparse.ArgumentParser(description="Run components of the model source code")
    subparsers = parser.add_subparsers()

    # TRAIN subparser
    sb_train = subparsers.add_parser("train_model", description="Train model")
    sb_train.set_defaults(func=my_main)

    args = parser.parse_args()
    args.func(args)
