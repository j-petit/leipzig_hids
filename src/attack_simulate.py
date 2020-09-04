"""
File: attack_simulate.py
Author: Jens Petit
Email: petit@informatik.uni-leipzig.de
Description: Running a simulated attack
"""


import pathpy
import pudb
import numpy as np

from src.RollingTimeWindow import MyRollingTimeWindow
from src.data_processing import generate_temporal_network

def trial_scenario(model, scenario : str, time_delta : int, window_size : int):
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

    temp_net = generate_temporal_network(scenario)

    windows = MyRollingTimeWindow(temp_net, window_size, step_size=100000, return_window=True)

    results = []

    print("Starting simulation...")

    for net, window in windows:

        print(net.summary())
        print(window)

        try:
            paths = pathpy.path_extraction.paths_from_temporal_network_single(net, delta=time_delta)

            if paths.paths:

                total_paths = 0

                for k in sorted(paths.paths):
                    paths_ = paths.paths[k]
                    if paths_:
                        values_ = np.array(list(paths_.values()))
                        v_0 = np.sum(values_[:, 0])
                        v_1 = np.sum(values_[:, 1])
                        total_paths += v_0 + v_1

                likelihood = model.likelihood(paths, log=True)
                likelihood /= total_paths
                results.append((likelihood, window[1]))
        except AttributeError as e:
            print("Skipping this window as no events...")
            print(e)
            continue
        except KeyError as e:
            print(f"Key {e} not found... Setting Likelihood to zero.")
            results.append((-100, window[1]))
        except pathpy.utils.exceptions.PathpyException as e:
            print(f"Key {e} not found... Setting Likelihood to zero.")
            results.append((-999, window[1]))

    return results
