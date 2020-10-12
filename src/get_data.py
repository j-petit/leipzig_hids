import os
from datetime import datetime
import pprint
import glob
import logging
import pickle
from pprint import pformat
import sys
import yaml
import pandas as pd

import sacred
from src.utils import config_adapt


ex = sacred.Experiment("pull_data")


@ex.config_hook
def hook(config, command_name, logger):
    config = config_adapt(config)
    config.update({'hook': True})
    return config


@ex.command(unobserved=True)
def print_config(_config):
    """ Replaces print_config which is not working with python 3.8 and current packages sacred"""
    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(_config)


@ex.automain
def get_dataset(hook, _config):
    """Downloads the dataset if it is not yet available and unzips it"""

    datasets = {
        "CVE-2014-0160": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/CVE-2014-0160.tar.gz",
        "PHP_CWE-434": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/PHP_CWE-434.tar.gz",
        "Bruteforce_CWE-307": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/Bruteforce_CWE-307.tar.gz",
        "SQL_Injection_CWE-89": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/SQL_Injection_CWE-89.tar.gz",
        "ZipSlip": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/ZipSlip.tar.gz",
        "CVE-2012-2122": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/CVE-2012-2122.tar.gz",
        "CVE-2017-7529": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/CVE-2017-7529.tar.gz",
        "CVE-2018-3760": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/CVE-2018-3760.tar.gz",
        "CVE-2019-5418": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/CVE-2019-5418.tar.gz",
        "EPS_CWE-434": "https://www.exploids.de/lid-ds-downloads/LID-DS-Recordings-01/EPS_CWE-434.tar.gz",
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
