import bidict


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
