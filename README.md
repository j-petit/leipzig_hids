# Host Intrusion Detection with Linux System Calls

This repository deals with using the statistical methods available through [Pathpy](https://www.pathpy.net/) for the host intrusion detection scenario. The dataset used is the [LID-DS](https://www.exploids.de/lid-ds/) which contains recordings of Linux system calls for attack and normal process execution. The applied methods are multi-order models as available in Pathpy.

## Install

I use conda to manage my python environment. Create a new environment from the `environment.yml`. To manage the experiment, [sacred](https://sacred.readthedocs.io/en/stable/) is used. For this, the connection to a MongoDB is established and results added to it. If you don't have access to the experiment MongoDB, specify the `-u` option and sacred can run without an observer.

The experiment is fully configured through one config file located in `config/config.yaml`. Here, different parts of the experiment (stages) can be switched on and off.

I extended pathpy with prior transition probabilities for all transitions which were not seen in the training data. To use it clone [the fork](https://github.com/j-petit/pathpy) and install it with
```
pip install -e .
```
while being in the cloned root folder and the hids conda environment (so pip of the environment is used).

## Running the experiment

Execute `python run.py` to execute the experiment. Only the defined stages will run. Use the `-u` flag to avoid creating an entry via sacred. The experiment config can be printed via

```
python run.py -u print_config
```

## Current State

There are five stages in the project:

1) `pull_data`: Downloads the corresponding data specified in the configuration file.
2) `analyze`: Runs a statistical evaluation of the data, focused on the time aspect.
3) `make_temp_paths`: Extracts paths from the system calls traces split based on a defined delta time.
4) `create_model`: Creates a pathpy multi-order model based on the temporal paths.
5) `simulate`: Tests a trained model with attack and non-attack runs and reports statistics back.

A thread separation of the system calls is done if a time-delta of 0 is specified.

## Data Analysis
For some insights into the data see [here](https://files.jenspetit.de/report/time_analysis.html). This is a hosted version of the document in `reports`.
