"""
File: attack_simulate.py
Author: Jens Petit
Email: petit@informatik.uni-leipzig.de
Description: Running a simulated scenario
"""


import pathpy
import numpy as np
import logging

from src.RollingTimeWindow import MyRollingTimeWindow
from src.data_processing import generate_temporal_network


def trial_scenario(model, scenario: str, time_delta: int, window_size: int):
    """Runs a scenario with a moving time window to simulate a running host intrusion detection.

    Parameters
    ----------
    model : pathpy.HigherOrderNetwork
        Created from regular training data
    scenario : str
        The path to the scenario to be evaluated
    time_delta : int
        Time-delta between syscalls in milliseconds to be considered a path
    window_size : int
        Time in milliseconds which is evaluated
    """

    results_logger = logging.getLogger("results")
    results_logger.info(f"Starting simulation with {scenario}")

    temp_net = generate_temporal_network(scenario)

    windows = MyRollingTimeWindow(temp_net, window_size, step_size=100000, return_window=True)

    likelihoods = []
    transitions = []
    time = []

    for net, window in windows:

        try:
            paths = pathpy.path_extraction.paths_from_temporal_network_single(net, delta=time_delta, max_subpath_length=3)

            total_transitions = 0

            if paths.paths:

                total_transitions = compute_total_transitions(paths)

                if total_transitions > 20:
                    time.append(window[0])
                    likelihood = model.likelihood(paths, log=True) / total_transitions
                    likelihoods.append(likelihood)
        except AttributeError as e:
            results_logger.info(f"Skipping ending at {window[1]} as no events...")
            likelihoods.append(-110)
            transitions.append(total_transitions)
            continue
        except KeyError as e:
            results_logger.info(f"Key {e} not found... Setting Likelihood to zero.")
            likelihoods.append(-100)
        except pathpy.utils.exceptions.PathpyException as e:
            results_logger.info(f"{e}... Setting Likelihood to 0")
            likelihoods.append(0)

        transitions.append(total_transitions)

    results = {"likelihoods": likelihoods, "transitions": transitions, "time": time}
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
