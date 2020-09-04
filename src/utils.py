import bidict
import yaml


def load_config(config: str):
    """Custom function to load a config file with additional constructor

    Parameters
    ----------
    config : str
        Path to the config.yaml file

    Returns
    -------
    config : dict
    """

    def join(loader, node):
        seq = loader.construct_sequence(node)
        return '/'.join([str(i) for i in seq])

    yaml.add_constructor('!join', join)
    with open(config, "r") as config_file:
        config = yaml.load(config_file, yaml.FullLoader)

    return config


def create_bidict(path: str):
    """Creates bidict object for mapping between syscall and integer. The string is the key.

    Parameters
    ----------
    path : str
        Location of textfile with two columns

    Returns
    -------
    bidict.bidict
    """

    temp_dict = {}

    with open(path) as raw_file:
        syscalls = raw_file.readlines()

    for i, syscall in enumerate(syscalls):
        temp_dict[syscall.strip()] = i

    return bidict.bidict(temp_dict)
