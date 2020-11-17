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


def get_dataset(config):
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

    os.makedirs(config["data"]["raw"], exist_ok=True)

    try:
        link = datasets[config["dataset"]]
    except KeyError as key:
        print("This dataset does not exist. Aborting.")
        print(f"The key was {key}")
        sys.exit(1)

    raw_data = os.path.join(config["data"]["prefix"], "raw")

    datapath = "{}/{}.tar.gz".format(raw_data, config["dataset"])

    print(datapath)

    if not os.path.exists(datapath):
        os.system(f"curl -LOJ {link}")
        os.system(f"mv {config['dataset']}.tar.gz {datapath}")
        os.system(f"tar -zxvf {datapath} -C {raw_data}")
        os.system(f"rm {datapath}")
