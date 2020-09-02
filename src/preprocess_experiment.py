import os
from datetime import datetime
import pprint
import glob
import logging
import pickle
from pprint import pformat
import sys

import pathpy

import src


def main(time_delta_selector):

    deltas = [5, 10, 15, 20, 25, 30]

    time_delta = deltas[time_delta_selector]

    dataset_runs = "data/CVE-2017-7529/runs.csv"

    paths = src.process_raw_temporal_dataset(dataset_runs, time_delta)

    pickle.dump(paths, open("data/" + f"temp_paths_{time_delta}.p", "wb"))

    print(paths)

    mog = pathpy.MultiOrderModel(paths, max_order=7)
    order = mog.estimate_order()

    hon = pathpy.HigherOrderNetwork(paths, k=order)

    print(hon)

    pickle.dump(hon, open("data/" + f"hon_{order}_delta_{time_delta}.p", "wb"))



if __name__ == "__main__":
    main(int(sys.argv[1]))
