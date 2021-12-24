from typing import Optional
import yaml
import os
import logging

def read_yml_file(file_path: str) -> Optional[dict]:
    """yaml file loader

    Args:
        file_path (str): path to .yml file

    Returns:
        Optional[dict]: content of file as dict
    """
    if not os.path.exists(file_path):
        logging.error(f"{file_path=} does not exist")
        return False
    with open(file_path) as file:
        try:
            loaded_dict = yaml.load(file, Loader=yaml.FullLoader)
        except (yaml.YAMLError, yaml.MarkedYAMLError):
            logging.error(f"{file_path=} not in yaml format")
            return False
        except Exception as err:
            logging.error(f"{err} occured while loading {file_path=}")
            return False
    return loaded_dict

