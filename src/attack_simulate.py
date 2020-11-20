"""
File: attack_simulate.py
Author: Jens Petit
Email: petit@informatik.uni-leipzig.de
Description: Running a scenario with a trained model
"""


from datetime import datetime
import logging
import pandas as pd
import numpy as np
import pathpy

from src.RollingTimeWindow import MyRollingTimeWindow
from src.data_processing import generate_temporal_network, generate_paths_from_threads, parse_run_to_pandas


def trial_scenario(model, run: str, time_delta: int, window_size: int):
    """Runs a run with a moving time window to simulate a running host intrusion detection.

    Parameters
    ----------
    model : pathpy.HigherOrderNetwork
        Created from regular training data
    run : str
        The path to the run to be evaluated
    time_delta : int
        Time-delta between syscalls in milliseconds to be considered a path. If time_delta is zero,
        then the paths will be extracted based on same threads.
    window_size : int
        Time in milliseconds which is evaluated
    """

    results_logger = logging.getLogger("hids.results")
    results_logger.debug(f"Starting simulation with {run}")

    temp_net = generate_temporal_network(run)
    windows = MyRollingTimeWindow(temp_net, window_size, step_size=100000, return_window=True)

    if time_delta == 0:
        run_data = parse_run_to_pandas(run)

    likelihoods = []
    transitions = []
    time = []

    for net, window in windows:

        try:
            if time_delta == 0:
                paths = generate_paths_from_threads(run_data, window)
            else:
                paths = pathpy.path_extraction.paths_from_temporal_network_single(
                    net, delta=time_delta, max_subpath_length=4
                )

            total_transitions = 0

            if paths.paths:

                total_transitions = compute_total_transitions(paths)

                # TODO: arbitrary threshold, put more thoughts into this
                if total_transitions > 3:

                    time.append(window[0])

                    # divide probability by number of transitions
                    likelihood = model.likelihood(paths, log=True) - np.log(total_transitions)
                    likelihoods.append(likelihood)

        except AttributeError as e:
            results_logger.info(f"Skipping ending at {window[1]} as no events...")
            likelihoods.append(-110)
            continue
        except KeyError as e:
            results_logger.info(f"Key {e} not found... Setting Likelihood to zero.")
            likelihoods.append(-100)
        except pathpy.utils.exceptions.PathpyException as e:
            results_logger.info(f"{e}... Setting Likelihood to 0")
            likelihoods.append(0)

        transitions.append(total_transitions)

    results = {"run": run, "likelihoods": likelihoods, "transitions": transitions, "time": time}
    return results


def compute_total_transitions(paths):
    """Computes the total number of nodes

    Parameters
    ----------
    paths : pathpy.Paths

    Returns
    -------
    total_paths : int
    """

    total_paths = 0
    lengths = paths.path_lengths()

    for key, value in lengths.items():
        total_paths += value[1] * (1 + key)

    return total_paths
