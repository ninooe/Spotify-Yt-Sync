import yaml
import logging
import os


def file2dict(file_path: str) -> dict:
    """yml file loader

    Args:
        file_path (str): path to .yml file

    Returns:
        dict: content of file as dict
    """
    if not os.path.exists(file_path):
        logging.error('No Configuration file provided!')
        return None
    with open(file_path) as file:
        # try to open file and check if yaml syntax is correct
        try:
            loaded_dict = yaml.load(file, Loader=yaml.FullLoader)
        except (yaml.YAMLError, yaml.MarkedYAMLError):
            logging.error("Config file not in YAML format!")
            return None
    return loaded_dict
