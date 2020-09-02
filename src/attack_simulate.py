"""
File: attack_simulate.py
Author: Jens Petit
Email: petit@informatik.uni-leipzig.de
Description: Running a simulated attack
"""


import pathpy
import src
import pudb

from src.RollingTimeWindow import MyRollingTimeWindow

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

    temp_net = src.generate_temporal_network(scenario)

    windows = MyRollingTimeWindow(temp_net, window_size, step_size=100, return_window=True)

    results = []

    print("Starting simulation...")

    for net, window in windows:

        print(net.summary())
        print(window)

        try:
            paths = pathpy.path_extraction.paths_from_temporal_network_single(net, delta=time_delta)
            likelihood = model.likelihood(paths, log=True)
            results.append((likelihood, window[1]))
        except AttributeError as e:
            print("Skipping this window as no events...")
            print(e)
            continue
        except KeyError as e:
            print(f"Key {e} not found... Setting Likelihood to zero.")
            results.append((-1.1, window[1]))

    return results
