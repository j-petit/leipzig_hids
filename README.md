# Host Intrusion Detection with Linux System Calls

## Install

I use conda to manage my python environment. Create a new environment from the `environment.yml`. To manage the experiment, [sacred](https://sacred.readthedocs.io/en/stable/) is used. For this, the connection to a MongoDB is established and results added to it.

The experiment is configured through one config file located in `config/config.yaml`. Here, different parts of the experiment (stages) can be switched on and off.

## Accessing the experiment results

One way to access the experiment results is via [Omniboard](https://vivekratnavel.github.io/omniboard/#/). For this, the port of the server has to be forwarded via ssh.

```
ssh -p 888 -L 9000:localhost:9000 guest@139.18.13.64
```

## Running experiments on a slurm cluster

For running a large number of experiments, a compute cluster with slurm can be used. For this the tool [seml](https://github.com/TUM-DAML/seml) is an excellent choice. An exemplary seml config file can be found at `config/seml_config.yaml`.
