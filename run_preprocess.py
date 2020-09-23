import argparse
import logging
import logging.config
import yaml

from src.preprocess_experiment import ex
from src.utils import load_config


if __name__ == "__main__":

    logging.config.fileConfig("config/logging_local.conf")
    logger = logging.getLogger("run")

    ex.run_commandline()
